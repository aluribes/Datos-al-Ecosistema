from pathlib import Path

import pandas as pd
import geopandas as gpd

# === CONFIGURACIÓN DE RUTAS ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_ROOT = BASE_DIR / "data" / "gold"

# Rutas de entrada (capa Gold base)
GEO_INPUT = GOLD_ROOT / "base" / "geo_gold.parquet"
POLICIA_INPUT = GOLD_ROOT / "base" / "policia_gold.parquet"
POBLACION_INPUT = GOLD_ROOT / "base" / "poblacion_gold.parquet"
DIVIPOLA_INPUT = GOLD_ROOT / "base" / "divipola_gold.parquet"

# Ruta de salida
GOLD_OUTPUT = GOLD_ROOT / "gold_integrado.parquet"


def ensure_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save(df: pd.DataFrame | gpd.GeoDataFrame, path: Path) -> None:
    ensure_folder(path.parent)
    df.to_parquet(path, index=False)


# Cargar GOLD/base
def load_gold_base() -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carga los datasets Gold/base.
    
    Nota: policia_gold ya viene complementado con datos de Socrata desde
    03_process_silver_data.py (función complementar_policia_con_socrata).
    No es necesario hacer fill_gaps aquí.
    """
    print("\n=== Cargando datasets Gold/base ===")
    geo = gpd.read_parquet(GEO_INPUT)
    policia = pd.read_parquet(POLICIA_INPUT)
    poblacion = pd.read_parquet(POBLACION_INPUT)
    divipola = pd.read_parquet(DIVIPOLA_INPUT)
    
    print(f"  Geografía:     {len(geo):>10,} registros")
    print(f"  Policía:       {len(policia):>10,} registros (ya incluye complementos de Socrata)")
    print(f"  Población:     {len(poblacion):>10,} registros")
    print(f"  Divipola:      {len(divipola):>10,} registros")
    
    # Mostrar origen de los datos de policía
    if "origen" in policia.columns:
        print("\n  Origen de datos policía:")
        for origen, count in policia["origen"].value_counts().items():
            pct = count / len(policia) * 100
            print(f"    {origen}: {count:,} ({pct:.1f}%)")
    
    return geo, policia, poblacion, divipola


# Integración GOLD
def integrate_gold(
    geo: gpd.GeoDataFrame,
    delitos: pd.DataFrame,
    poblacion: pd.DataFrame,
    divipola: pd.DataFrame
) -> gpd.GeoDataFrame:
    """
    Integra todos los datasets Gold en un único DataFrame.
    
    Args:
        geo: Geografía de municipios
        delitos: Delitos integrados (scraping + socrata gaps)
        poblacion: Datos demográficos
        divipola: Centros poblados
    """
    print("\n=== Integrando Gold ===")
    print("➤ Agregando centros poblados…")
    centros = (
        divipola.groupby("codigo_municipio")
        .agg(n_centros_poblados=("codigo_centro_poblado", "count"))
        .reset_index()
    )

    df = geo.merge(centros, on="codigo_municipio", how="left")
    df["n_centros_poblados"] = df["n_centros_poblados"].fillna(0)

    # Agregar delitos (esto SI genera anio y mes)
    print("➤ Agregando delitos (municipio-año-mes)…")

    delitos_agg = (
        delitos.groupby(["codigo_municipio", "anio", "mes"])
        .agg(total_delitos=("cantidad", "sum"))
        .reset_index()
    )

    df = df.merge(delitos_agg, on="codigo_municipio", how="left")

    # Pivot delitos por tipo
    print("➤ Pivot delitos por tipo…")

    delitos_tipo = (
        delitos.pivot_table(
            index=["codigo_municipio", "anio", "mes"],
            columns="delito",
            values="cantidad",
            aggfunc="sum",
            fill_value=0,
            observed=False
        )
        .reset_index()
    )

    df = df.merge(delitos_tipo, on=["codigo_municipio", "anio", "mes"], how="left")

    # Población: pivot solo por año
    print("➤ Pivoteando población (municipio-año)…")

    demo = (
        poblacion.pivot_table(
            index=["codigo_municipio", "anio"],
            columns=["genero", "grupo_edad"],
            values="n_poblacion",
            aggfunc="sum",
            fill_value=0,
            observed=False
        )
        .reset_index()
    )

    # Renombrar columnas *sin perder código ni año*
    new_cols = ["codigo_municipio", "anio"] + [
        f"{g}_{e}".lower().replace(" ", "_")
        for (g, e) in demo.columns[2:]
    ]
    demo.columns = new_cols

    # Agregados demográficos
    demo["poblacion_total"] = demo.filter(regex="femenino|masculino").sum(axis=1)
    demo["poblacion_menores"] = demo.filter(like="menores").sum(axis=1)
    demo["poblacion_adultos"] = demo.filter(like="adultos").sum(axis=1)
    demo["poblacion_adolescentes"] = demo.filter(like="adolescentes").sum(axis=1)

    df = df.merge(demo, on=["codigo_municipio", "anio"], how="left")

    # Variables derivadas
    print("➤ Calculando métricas…")

    df["area_km2"] = df["area"]
    df["densidad_poblacional"] = df["poblacion_total"] / df["area_km2"]
    df["centros_por_km2"] = df["n_centros_poblados"] / df["area_km2"]

    df["proporcion_menores"] = df["poblacion_menores"] / df["poblacion_total"]
    df["proporcion_adultos"] = df["poblacion_adultos"] / df["poblacion_total"]
    df["proporcion_adolescentes"] = df["poblacion_adolescentes"] / df["poblacion_total"]

    df["fecha"] = pd.to_datetime(
        df["anio"].astype(str) + "-" + df["mes"].astype(str) + "-01",
        errors="coerce"
    )
    df["trimestre"] = df["fecha"].dt.quarter
    df["anio_mes"] = df["fecha"].dt.to_period("M").astype(str)
    df["es_fin_ano"] = (df["mes"] == 12).astype(int)

    # --- Conteos mensuales de días (agregados desde delitos) ---
    print("➤ Agregando conteos mensuales de días…")

    dias_agg = (
        delitos.groupby(["codigo_municipio", "anio", "mes"])
        .agg(
            n_dias_semana=("es_dia_semana", "sum"),
            n_fines_de_semana=("es_fin_de_semana", "sum"),
            n_festivos=("es_festivo", "sum"),
            n_dias_laborales=("es_dia_laboral", "sum"),
        )
        .reset_index()
    )

    df = df.merge(dias_agg, on=["codigo_municipio", "anio", "mes"], how="left")

    return df


# Ejecutar gold integrado y guardarlo
def make_gold() -> None:
    print("=" * 60)
    print("🥇 GENERACIÓN DE GOLD INTEGRADO")
    print("=" * 60)
    
    # Cargar datos (policia ya viene complementado desde 03_process_silver_data.py)
    geo, policia, poblacion, divipola = load_gold_base()
    
    # Generar gold integrado usando policia directamente (ya está completo)
    df_gold = integrate_gold(geo, policia, poblacion, divipola)
    
    # Guardar
    save(df_gold, GOLD_OUTPUT)
    
    # Reporte final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    print(f"  Registros gold_integrado: {len(df_gold):,}")
    print(f"  Columnas: {len(df_gold.columns)}")
    print(f"  Período: {df_gold['anio'].min()} - {df_gold['anio'].max()}")
    print(f"  Municipios: {df_gold['codigo_municipio'].nunique()}")
    
    # Origen de datos
    if "origen" in policia.columns:
        origen_counts = policia['origen'].value_counts()
        print("\n  Origen de delitos:")
        for origen, count in origen_counts.items():
            pct = count / len(policia) * 100
            print(f"    {origen}: {count:,} ({pct:.1f}%)")
    
    print("=" * 60)
    print("✔ gold_integrado.parquet generado con éxito.")


if __name__ == "__main__":
    make_gold()
