import pandas as pd
import geopandas as gpd
from pathlib import Path
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
gold_root = os.path.join(BASE_DIR, "data", "gold")


def ensure_folder(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def save(df, path):
    ensure_folder(Path(path).parent)
    df.to_parquet(path, index=False)


# Load GOLD Integrado
def load_gold_integrado():
    path = os.path.join(gold_root, "gold_integrado.parquet")
    print(f"✔ Cargando GOLD integrado: {path}")
    return gpd.read_parquet(path)


# Generar indicadores analíticos
def build_analytics(df):

    print("➤ Calculando tasas de delito por 100.000 habitantes…")

    delitos_base = [
        "ABIGEATO", "HURTOS", "LESIONES",
        "VIOLENCIA INTRAFAMILIAR", "AMENAZAS",
        "DELITOS SEXUALES", "EXTORSION", "HOMICIDIOS"
    ]

    for col in delitos_base:
        if col in df.columns:
            df[f"tasa_{col.lower().replace(' ', '_')}"] = (
                df[col] / df["poblacion_total"] * 100000
            )

    print("➤ Calculando indicadores espaciales y demográficos…")

    df["densidad_poblacional"] = df["poblacion_total"] / df["area_km2"]
    df["centros_por_km2"] = df["n_centros_poblados"] / df["area_km2"]

    df["proporcion_menores"] = df["poblacion_menores"] / df["poblacion_total"]
    df["proporcion_adultos"] = df["poblacion_adultos"] / df["poblacion_total"]
    df["proporcion_adolescentes"] = df["poblacion_adolescentes"] / df["poblacion_total"]

    return df



# Ejecucion para generar analiticos
def make_analytics():

    df = load_gold_integrado()
    df_analytics = build_analytics(df)

    save(df_analytics, os.path.join(gold_root, "analytics", "gold_analytics.parquet"))
    print("✔ gold_analytics.parquet generado.")


if __name__ == "__main__":
    make_analytics()
