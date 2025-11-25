import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from pathlib import Path
import os
import sys

# Ruta base 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
silver_root = os.path.join(BASE_DIR, "data", "silver")
gold_root   = os.path.join(BASE_DIR, "data", "gold")

# Utilidades 
def ensure_folder(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def save(df, path):
    ensure_folder(Path(path).parent)
    df.to_parquet(path, index=False)

def check_exists(path, label=None):
    if not os.path.exists(path):
        msg = f"ERROR: No se encontró el archivo requerido:\n{path}"
        if label:
            msg += f"\n(dataset: {label})"
        print(msg)
        sys.exit(1)
    else:
        print(f"✔ Archivo encontrado: {path}")

# Carga única de los datasets Silver

def load_silver():
    print("\n=== Verificando archivos Silver ===")

    geo_path = os.path.join(silver_root, "dane_geo", "geografia_silver.parquet")
    policia_path = os.path.join(silver_root, "policia_scraping", "policia_santander.parquet")
    poblacion_path = os.path.join(silver_root, "poblacion", "poblacion_santander.parquet")
    divipola_path = os.path.join(silver_root, "dane_geo", "divipola_silver.parquet")

    # Verificaciones previas
    check_exists(geo_path, "geografia (geo)")
    check_exists(policia_path, "policia scraping")
    check_exists(poblacion_path, "poblacion santander")
    check_exists(divipola_path, "divipola")

    print("\n=== Cargando datasets Silver ===")
    geo = gpd.read_parquet(geo_path)
    policia = pd.read_parquet(policia_path)
    poblacion = pd.read_parquet(poblacion_path)
    divipola = pd.read_parquet(divipola_path)

    return geo, policia, poblacion, divipola

# Limpieza de cada dataset

def clean_names(df, cols=["municipio", "departamento"]):
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

def clean_geo(geo):
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


def clean_policia(df):

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
        df["ds"] = df["fecha"].dt.dayofweek
        df["fds"] = df["ds"].isin([5, 6]).astype(int)

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



def clean_poblacion(df):
    df["codigo_municipio"] = pd.to_numeric(df["codigo_municipio"], errors="coerce").astype("Int64")
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df = clean_names(df)
    return df


def clean_divipola(df):
    df["codigo_municipio"] = pd.to_numeric(df["codigo_municipio"], errors="coerce").astype("Int64")
    df = clean_names(df)
    return df

    return df


# Ejecutar transformación completa Silver → Gold/base

def prepare_silver_to_gold():

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
    save(geo, os.path.join(gold_root, "base", "geo_gold.parquet"))
    save(policia, os.path.join(gold_root, "base", "policia_gold.parquet"))
    save(poblacion, os.path.join(gold_root, "base", "poblacion_gold.parquet"))
    save(divipola, os.path.join(gold_root, "base", "divipola_gold.parquet"))

    print("✔ Limpieza y exportación completadas.")


if __name__ == "__main__":
    prepare_silver_to_gold()
