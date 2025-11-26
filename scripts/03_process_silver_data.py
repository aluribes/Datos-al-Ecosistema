from pathlib import Path
import sys

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
import holidays

# === CONFIGURACIÓN DE RUTAS ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
SILVER_ROOT = BASE_DIR / "data" / "silver"
GOLD_ROOT = BASE_DIR / "data" / "gold"

# Rutas de entrada (capa Silver)
GEO_INPUT = SILVER_ROOT / "dane_geo" / "geografia_silver.parquet"
POLICIA_INPUT = SILVER_ROOT / "policia_scraping" / "policia_santander.parquet"
POBLACION_INPUT = SILVER_ROOT / "poblacion" / "poblacion_santander.parquet"
DIVIPOLA_INPUT = SILVER_ROOT / "dane_geo" / "divipola_silver.parquet"

# Rutas de salida (capa Gold base)
GEO_OUTPUT = GOLD_ROOT / "base" / "geo_gold.parquet"
POLICIA_OUTPUT = GOLD_ROOT / "base" / "policia_gold.parquet"
POBLACION_OUTPUT = GOLD_ROOT / "base" / "poblacion_gold.parquet"
DIVIPOLA_OUTPUT = GOLD_ROOT / "base" / "divipola_gold.parquet"


# Utilidades 
def ensure_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save(df: pd.DataFrame | gpd.GeoDataFrame, path: Path) -> None:
    ensure_folder(path.parent)
    df.to_parquet(path, index=False)

def check_exists(path: Path, label: str | None = None) -> None:
    if not path.exists():
        msg = f"ERROR: No se encontró el archivo requerido:\n{path}"
        if label:
            msg += f"\n(dataset: {label})"
        print(msg)
        sys.exit(1)
    else:
        print(f"✔ Archivo encontrado: {path}")

# Carga única de los datasets Silver

def load_silver() -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    print("\n=== Verificando archivos Silver ===")

    # Verificaciones previas
    check_exists(GEO_INPUT, "geografia (geo)")
    check_exists(POLICIA_INPUT, "policia scraping")
    check_exists(POBLACION_INPUT, "poblacion santander")
    check_exists(DIVIPOLA_INPUT, "divipola")

    print("\n=== Cargando datasets Silver ===")
    geo = gpd.read_parquet(GEO_INPUT)
    policia = pd.read_parquet(POLICIA_INPUT)
    poblacion = pd.read_parquet(POBLACION_INPUT)
    divipola = pd.read_parquet(DIVIPOLA_INPUT)

    return geo, policia, poblacion, divipola

# Limpieza de cada dataset

def clean_names(df: pd.DataFrame, cols: list[str] = ["municipio", "departamento"]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = (
                df[c]
                .astype(str)
                .str.strip()
                .str.upper()
                .replace({"NAN": np.nan})
            )
    return df

def clean_geo(geo: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # Eliminar nulos de geometría y reparar
    geo = geo[geo.geometry.notnull()].copy()
    geo["geometry"] = geo["geometry"].buffer(0)
    if geo.crs is None:
        geo.set_crs("EPSG:4326", inplace=True)
    geo = geo.explode(index_parts=False)

    # Convertir llave a Int64
    geo["codigo_municipio"] = (
        pd.to_numeric(geo["codigo_municipio"], errors="coerce").astype("Int64")
    )

    # Estandarizar nombres
    geo = clean_names(geo)

    return geo


def clean_policia(df: pd.DataFrame) -> pd.DataFrame:

    df["codigo_dane"] = df["codigo_dane"].astype(str).str.strip()

    df["codigo_dane"] = df["codigo_dane"].apply(
        lambda x: x[:-3] if isinstance(x, str) and len(x) > 3 else x
    )

    df["codigo_dane"] = df["codigo_dane"].str.replace(r"\D+", "", regex=True)

    df["codigo_municipio"] = pd.to_numeric(
        df["codigo_dane"], errors="coerce"
    ).astype("Int64")

    df = clean_names(df)

    # --- Procesar fecha ---
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

        df["anio"] = df["fecha"].dt.year.astype("Int64")
        df["mes"] = df["fecha"].dt.month.astype("Int64")
        df["dia"] = df["fecha"].dt.day.astype("Int64")

        # --- Día de la semana y fin de semana ---
        dia_semana = df["fecha"].dt.dayofweek
        df["es_dia_semana"] = (dia_semana < 5).astype(int)
        df["es_fin_de_semana"] = (dia_semana >= 5).astype(int)

        # --- Fin de mes ---
        df["es_fin_mes"] = (df["dia"] == df["fecha"].dt.days_in_month).astype(int)

        # --- Festivos colombianos ---
        anios = df["anio"].dropna().unique().tolist()
        if anios:
            col_holidays = holidays.Colombia(years=[int(a) for a in anios])
            df["es_festivo"] = df["fecha"].apply(
                lambda x: 1 if pd.notna(x) and x in col_holidays else 0
            )
            df["nombre_festivo"] = df["fecha"].apply(
                lambda x: col_holidays.get(x, None) if pd.notna(x) else None
            )
        else:
            df["es_festivo"] = 0
            df["nombre_festivo"] = None

        # --- Día laboral (día de semana y no festivo) ---
        df["es_dia_laboral"] = ((df["es_dia_semana"] == 1) & (df["es_festivo"] == 0)).astype(int)

    # categorías
    for col in ["genero", "armas_medios", "delito", "edad_persona"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.upper()
                .replace({"NAN": np.nan})
                .astype("category")
            )

    # eliminar campo viejo
    df = df.drop(columns=["codigo_dane"], errors="ignore")

    return df



def clean_poblacion(df: pd.DataFrame) -> pd.DataFrame:
    df["codigo_municipio"] = pd.to_numeric(df["codigo_municipio"], errors="coerce").astype("Int64")
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df = clean_names(df)
    return df


def clean_divipola(df: pd.DataFrame) -> pd.DataFrame:
    df["codigo_municipio"] = pd.to_numeric(df["codigo_municipio"], errors="coerce").astype("Int64")
    df = clean_names(df)
    return df

    return df


# Ejecutar transformación completa Silver → Gold/base

def prepare_silver_to_gold() -> None:

    print("Cargando datos Silver…")
    geo, policia, poblacion, divipola = load_silver()

    print("Limpiando Geografia…")
    geo = clean_geo(geo)

    print("Limpiando Policía…")
    policia = clean_policia(policia)

    print("Limpiando Población…")
    poblacion = clean_poblacion(poblacion)

    print("Limpiando Divipola…")
    divipola = clean_divipola(divipola)

    print("Guardando en data/gold/base…")
    save(geo, GEO_OUTPUT)
    save(policia, POLICIA_OUTPUT)
    save(poblacion, POBLACION_OUTPUT)
    save(divipola, DIVIPOLA_OUTPUT)

    print("✔ Limpieza y exportación completadas.")


if __name__ == "__main__":
    prepare_silver_to_gold()
