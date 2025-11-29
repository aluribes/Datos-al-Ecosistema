"""
04_generate_dashboard_data.py
=============================

Genera los datasets de la capa GOLD específicos para el dashboard.

Entrada (Silver):
    - data/silver/dane_geo/geografia_silver.parquet
    - data/silver/metas/*.parquet
    - data/silver/poblacion/poblacion_santander.parquet
    - data/silver/policia_scraping/policia_santander.parquet
    - data/silver/socrata_api/delitos_informaticos.parquet
    - data/silver/socrata_api/delitos_bucaramanga.parquet

Salida (Gold / dashboard):
    - data/gold/dashboard/municipios.parquet
    - data/gold/dashboard/<mismos nombres de metas>.parquet
    - data/gold/dashboard/poblacion_santander.parquet
    - data/gold/dashboard/policia_santander.parquet
    - data/gold/dashboard/delitos_informaticos.parquet
    - data/gold/dashboard/delitos_bucaramanga.parquet
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Tuple

import pandas as pd
import geopandas as gpd
import numpy as np
import holidays


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
SILVER_ROOT = BASE_DIR / "data" / "silver"
GOLD_DASHBOARD_ROOT = BASE_DIR / "data" / "gold" / "dashboard"

# Entradas Silver
GEO_INPUT = SILVER_ROOT / "dane_geo" / "geografia_silver.parquet"
METAS_DIR = SILVER_ROOT / "metas"
POBLACION_INPUT = SILVER_ROOT / "poblacion" / "poblacion_santander.parquet"
POLICIA_INPUT = SILVER_ROOT / "policia_scraping" / "policia_santander.parquet"
DELITOS_INF_INPUT = SILVER_ROOT / "socrata_api" / "delitos_informaticos.parquet"
DELITOS_BUCA_INPUT = SILVER_ROOT / "socrata_api" / "delitos_bucaramanga.parquet"

# Salidas Gold / dashboard
MUNICIPIOS_OUTPUT = GOLD_DASHBOARD_ROOT / "municipios.parquet"
POBLACION_OUTPUT = GOLD_DASHBOARD_ROOT / "poblacion_santander.parquet"
POLICIA_OUTPUT = GOLD_DASHBOARD_ROOT / "policia_santander.parquet"
DELITOS_INF_OUTPUT = GOLD_DASHBOARD_ROOT / "delitos_informaticos.parquet"
DELITOS_BUCA_OUTPUT = GOLD_DASHBOARD_ROOT / "delitos_bucaramanga.parquet"


# ============================================================
# UTILIDADES
# ============================================================

def ensure_folder(path: Path) -> None:
    """Crea el directorio padre si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def check_exists(path: Path, label: str | None = None) -> None:
    """Verifica que un archivo exista antes de procesarlo."""
    if not path.exists():
        msg = f"❌ ERROR: No se encontró el archivo requerido:\n{path}"
        if label:
            msg += f"\n(dataset: {label})"
        print(msg)
        sys.exit(1)
    print(f"✔ Archivo encontrado: {path}")


def save_parquet(df: pd.DataFrame | gpd.GeoDataFrame, path: Path) -> None:
    """Guarda un DataFrame/GeoDataFrame en parquet en la ruta indicada."""
    ensure_folder(path.parent)
    df.to_parquet(path, index=False)
    print(f"   ✅ Guardado en: {path} (filas: {len(df):,})")


def add_temporal_features(
    df: pd.DataFrame,
    date_col: str = "fecha",
    prefix_log: str = "",
) -> pd.DataFrame:
    """
    A partir de una columna de fecha, agrega:
        - anio, mes, dia
        - es_dia_semana, es_fin_de_semana
        - es_fin_mes
        - es_festivo, nombre_festivo
        - es_dia_laboral
    """
    df = df.copy()

    if date_col not in df.columns:
        print(f"{prefix_log}⚠ No se encontró la columna '{date_col}', no se agregan campos temporales.")
        return df

    print(f"{prefix_log}Procesando columna de fecha '{date_col}'...")

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # anio, mes, dia
    df["anio"] = df[date_col].dt.year.astype("Int64")
    df["mes"] = df[date_col].dt.month.astype("Int64")
    df["dia"] = df[date_col].dt.day.astype("Int64")

    # Día de la semana (0 = lunes, 6 = domingo)
    dia_semana = df[date_col].dt.dayofweek
    df["es_dia_semana"] = (dia_semana < 5).astype("Int64")
    df["es_fin_de_semana"] = (dia_semana >= 5).astype("Int64")

    # Fin de mes
    df["es_fin_mes"] = (df["dia"] == df[date_col].dt.days_in_month).astype("Int64")

    # Festivos colombianos
    years = df["anio"].dropna().unique().tolist()
    if years:
        co_holidays = holidays.Colombia(years=[int(y) for y in years])
        df["es_festivo"] = df[date_col].apply(
            lambda x: 1 if pd.notna(x) and x in co_holidays else 0
        ).astype("Int64")
        df["nombre_festivo"] = df[date_col].apply(
            lambda x: co_holidays.get(x, None) if pd.notna(x) else None
        )
    else:
        df["es_festivo"] = 0
        df["nombre_festivo"] = None

    # Día laboral: día de semana y no festivo
    df["es_dia_laboral"] = (
        (df["es_dia_semana"] == 1) & (df["es_festivo"] == 0)
    ).astype("Int64")

    return df


# ============================================================
# PROCESOS ESPECÍFICOS
# ============================================================

def process_municipios() -> None:
    """Copia geografia_silver a municipios.parquet en GOLD/dashboard."""
    print("\n" + "=" * 60)
    print("🏙  GENERANDO MUNICIPIOS (geografia_silver → municipios.parquet)")
    print("=" * 60)

    check_exists(GEO_INPUT, "geografia_silver")
    geo = gpd.read_parquet(GEO_INPUT)

    # 👉 NUEVO: asegurar codigo_municipio como Int64
    if "codigo_municipio" in geo.columns:
        geo["codigo_municipio"] = (
            pd.to_numeric(geo["codigo_municipio"], errors="coerce").astype("Int64")
        )

    save_parquet(geo, MUNICIPIOS_OUTPUT)


def process_metas() -> None:
    """Copia todos los .parquet de data/silver/metas a data/gold/dashboard."""
    print("\n" + "=" * 60)
    print("🎯 COPIANDO METAS (Silver → Gold/dashboard)")
    print("=" * 60)

    if not METAS_DIR.exists():
        print(f"⚠ No existe el directorio de metas: {METAS_DIR}")
        return

    parquet_files = sorted(METAS_DIR.glob("*.parquet"))
    if not parquet_files:
        print(f"⚠ No se encontraron archivos .parquet en {METAS_DIR}")
        return

    for src in parquet_files:
        print(f"➤ Copiando metas: {src.name}")
        df = pd.read_parquet(src)
        dst = GOLD_DASHBOARD_ROOT / src.name
        save_parquet(df, dst)


def process_poblacion() -> None:
    """
    Copia poblacion_santander.parquet a GOLD/dashboard,
    asegurando que 'anio' (y opcionalmente 'codigo_municipio')
    queden como tipo numérico Int64.
    """
    print("\n" + "=" * 60)
    print("👥 COPIANDO POBLACIÓN (Silver → Gold/dashboard)")
    print("=" * 60)

    check_exists(POBLACION_INPUT, "poblacion_santander")
    df = pd.read_parquet(POBLACION_INPUT).copy()

    # 👉 AQUÍ normalizamos tipos
    if "anio" in df.columns:
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")

    if "codigo_municipio" in df.columns:
        df["codigo_municipio"] = (
            pd.to_numeric(df["codigo_municipio"], errors="coerce").astype("Int64")
        )

    save_parquet(df, POBLACION_OUTPUT)


def process_policia() -> None:
    """
    Procesa data/silver/policia_scraping/policia_santander.parquet:
        - Normaliza codigo_municipio a Int64
        - Agrega columnas temporales basadas en 'fecha'
        - Guarda en data/gold/dashboard/policia_santander.parquet
    """
    print("\n" + "=" * 60)
    print("🚓 PROCESANDO POLICÍA (policia_santander → dashboard)")
    print("=" * 60)

    check_exists(POLICIA_INPUT, "policia_santander")
    df = pd.read_parquet(POLICIA_INPUT).copy()

    # 👉 NUEVO: asegurar codigo_municipio como Int64
    if "codigo_municipio" in df.columns:
        df["codigo_municipio"] = (
            pd.to_numeric(df["codigo_municipio"], errors="coerce").astype("Int64")
        )

    df = add_temporal_features(df, date_col="fecha", prefix_log="   ")

    save_parquet(df, POLICIA_OUTPUT)


def process_delitos_informaticos() -> None:
    """
    Procesa data/silver/socrata_api/delitos_informaticos.parquet:
        - Agrega columnas temporales basadas en 'fecha'
        - Guarda en data/gold/dashboard/delitos_informaticos.parquet
    """
    print("\n" + "=" * 60)
    print("💻 PROCESANDO DELITOS INFORMÁTICOS → dashboard")
    print("=" * 60)

    check_exists(DELITOS_INF_INPUT, "delitos_informaticos")
    df = pd.read_parquet(DELITOS_INF_INPUT)

    df = add_temporal_features(df, date_col="fecha", prefix_log="   ")

    save_parquet(df, DELITOS_INF_OUTPUT)


def build_fecha_from_parts(
    df: pd.DataFrame,
    year_col: str = "anio",
    month_col: str = "mes",
    day_col: str = "dia",
) -> pd.Series:
    """
    Construye una Serie de fechas a partir de columnas anio/mes/dia.
    Cualquier combinación inválida se convierte en NaT.
    """
    aux = pd.DataFrame(index=df.index)
    aux["year"] = pd.to_numeric(df.get(year_col), errors="coerce")
    aux["month"] = pd.to_numeric(df.get(month_col), errors="coerce")
    aux["day"] = pd.to_numeric(df.get(day_col), errors="coerce")

    mask_valid = aux[["year", "month", "day"]].notna().all(axis=1)

    fecha = pd.to_datetime(
        dict(
            year=aux.loc[mask_valid, "year"].astype(int),
            month=aux.loc[mask_valid, "month"].astype(int),
            day=aux.loc[mask_valid, "day"].astype(int),
        ),
        errors="coerce",
    )

    fecha_full = pd.Series(pd.NaT, index=df.index)
    fecha_full.loc[mask_valid] = fecha

    return fecha_full

# (todo lo de map_delito_bucaramanga y process_delitos_bucaramanga
# se mantiene igual que ya lo tenías)

def map_delito_bucaramanga(valor: str) -> str:
    """
    Clasifica el delito detallado en una categoría estándar:
        - DELITOS SEXUALES
        - DELITOS
        - EXTORSION
        - HOMICIDIOS
        - HURTOS
        - LESIONES

    Si no encuentra coincidencia, devuelve el valor original.
    """
    if not isinstance(valor, str):
        return valor

    v = valor.strip().upper()

    delitos_sexuales = {
        "ACCESO CARNAL ABUSIVO CON MENOR DE 14 AÑOS",
        "ACCESO CARNAL ABUSIVO CON MENOR DE 14 AÑOS (CIRCUNSTANCIAS AGRAVACIÓN)",
        "ACCESO CARNAL O ACTO SEXUAL ABUSIVO CON INCAPAZ DE RESISTIR",
        "ACCESO CARNAL O ACTO SEXUAL ABUSIVO CON INCAPAZ DE RESISTIR (CIRCUNSTANCIAS AGRAVACIÓN)",
        "ACCESO CARNAL O ACTO SEXUAL EN PERSONA PUESTA EN INCAPACIDAD DE RESISTIR",
        "ACCESO CARNAL O ACTO SEXUAL EN PERSONA PUESTA EN INCAPACIDAD DE RESISTIR  (CIRCUNSTANC",
        "ACCESO CARNAL VIOLENTO",
        "ACCESO CARNAL VIOLENTO (CIRCUNSTANCIAS AGRAVACIÓN)",
        "ACOSO SEXUAL",
        "ACTO SEXUAL VIOLENTO",
        "ACTO SEXUAL VIOLENTO (CIRCUNSTANCIAS DE AGRAVACIÓN)",
        "ACTOS SEXUALES CON MENOR DE 14 AÑOS",
        "ACTOS SEXUALES CON MENOR DE 14 AÑOS (CIRCUNSTANCIAS DE AGRAVACIÓN)",
        "CONSTREÑIMIENTO A LA PROSTITUCIÓN",
        "DEMANDA DE EXPLOTACION SEXUAL COMERCIAL DE PERSONA MENOR DE 18 AÑOS DE EDAD",
        "ESTÍMULO A LA PROSTITUCIÓN DE MENORES",
        "INDUCCIÓN A LA PROSTITUCIÓN",
        "PORNOGRAFÍA CON MENORES",
        "PROXENETISMO CON MENOR DE EDAD",
        "UTILIZACIÓN O FACILITACIÓN DE MEDIOS DE COMUNICACIÓN PARA OFRECER SERVICIOS SEXUALES DE MENORES",
        "VIOLENCIA SEXUAL",
    }

    delitos_generales = {
        "DAÑO EN BIEN AJENO",
        "INCENDIO",
        "VIOLENCIA CONTRA SERVIDOR PÚBLICO",
        "TERRORISMO",
    }

    extorsion = {
        "EXTORSIÓN",
    }

    homicidios = {
        "HOMICIDIO CULPOSO ( EN ACCIDENTE DE TRÁNSITO)",
        "HOMICIDIO",
        "FEMINICIDIO",
        "MUERTE EN ACCIDENTE DE TRANSITO",
    }

    hurtos = {
        "HURTO AUTOMOTORES",
        "HURTO ENTIDADES COMERCIALES",
        "HURTO MOTOCICLETAS",
        "HURTO PERSONAS",
        "HURTO RESIDENCIAS",
    }

    lesiones = {
        "LESION ACCIDENTAL EN TRANSITO",
        "LESIONES AL FETO",
        "LESIONES CULPOSAS",
        "LESIONES CULPOSAS ( EN ACCIDENTE DE TRANSITO )",
        "LESIONES FATALES",
        "LESIONES NO FATALES",
        "LESIONES PERSONALES",
        "LESIONES PERSONALES ( CIRCUNSTANCIAS DE AGRAVACIÓN)",
    }

    if v in delitos_sexuales:
        return "DELITOS SEXUALES"
    if v in delitos_generales:
        return "DELITOS"
    if v in extorsion:
        return "EXTORSION"
    if v in homicidios:
        return "HOMICIDIOS"
    if v in hurtos:
        return "HURTOS"
    if v in lesiones:
        return "LESIONES"

    return v


def process_delitos_bucaramanga() -> None:
    """
    Procesa data/silver/socrata_api/delitos_bucaramanga.parquet:

    - Limpia y clasifica la columna 'delito' en categorías estándar.
    - Elimina registros donde el delito sea NO REPORTA u OMISIÓN DE DENUNCIA.
    - Completa/usa 'fecha' con información de anio/mes/dia si es necesario.
    - Agrega campos temporales (anio, mes, dia, es_dia_semana, etc.).
    - Agrega codigo_municipio = 68001 y municipio = "BUCARAMANGA".
    - Guarda como data/gold/dashboard/delitos_bucaramanga.parquet
    """
    print("\n" + "=" * 60)
    print("🏙  PROCESANDO DELITOS BUCARAMANGA → dashboard")
    print("=" * 60)

    check_exists(DELITOS_BUCA_INPUT, "delitos_bucaramanga")
    df = pd.read_parquet(DELITOS_BUCA_INPUT).copy()

    if "delito" in df.columns:
        df["delito"] = df["delito"].astype(str).str.strip().str.upper()

        mask_drop = (
            df["delito"].str.contains("NO REPORTA", case=False, na=False)
            | df["delito"].str.contains("OMISIÓN DE DENUNCIA", case=False, na=False)
            | df["delito"].str.contains("OMISION DE DENUNCIA", case=False, na=False)
        )
        before = len(df)
        df = df[~mask_drop].copy()
        removed = before - len(df)
        print(f"   Registros eliminados por NO REPORTA / OMISIÓN DE DENUNCIA: {removed:,}")

        df["delito"] = df["delito"].apply(map_delito_bucaramanga)
    else:
        print("   ⚠ La tabla delitos_bucaramanga no tiene columna 'delito'.")

    df["codigo_municipio"] = pd.Series(68001, index=df.index, dtype="Int64")
    df["municipio"] = "BUCARAMANGA"

    if "fecha" in df.columns:
        fecha = pd.to_datetime(df["fecha"], errors="coerce")
    else:
        fecha = pd.Series(pd.NaT, index=df.index)

    mask_fecha_na = fecha.isna()
    has_ymd_cols = all(col in df.columns for col in ["anio", "mes", "dia"])

    if has_ymd_cols:
        print("   Usando columnas anio/mes/dia para completar fechas faltantes...")
        fecha_from_parts = build_fecha_from_parts(df)
        fecha.loc[mask_fecha_na] = fecha_from_parts.loc[mask_fecha_na]

    df["fecha"] = fecha

    df = add_temporal_features(df, date_col="fecha", prefix_log="   ")

    save_parquet(df, DELITOS_BUCA_OUTPUT)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 60)
    print("04 - GENERACIÓN DE DATOS PARA DASHBOARD (GOLD/dashboard)")
    print("=" * 60)

    process_municipios()
    process_metas()
    process_poblacion()
    process_policia()
    process_delitos_informaticos()
    process_delitos_bucaramanga()

    print("\n" + "=" * 60)
    print("✔ Generación de datos para dashboard completada")
    print("=" * 60)


if __name__ == "__main__":
    main()
