"""
Genera dataset geográfico para modelos de regresión espacial.
Entrada:  data/gold/gold_integrado.parquet
Salida:   data/gold/models/regression_geo.parquet

Incluye:
- Variables demográficas
- Variables espaciales
- Área, densidad, proporciones poblacionales
- Total de delitos y tasas por delito (promedio anual)
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

INPUT_FILE = GOLD_DIR / "gold_integrado.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "regression_geo.parquet"

DELITOS = [
    "ABIGEATO","HURTOS","LESIONES","VIOLENCIA INTRAFAMILIAR",
    "AMENAZAS","DELITOS SEXUALES","EXTORSION","HOMICIDIOS"
]

def ensure_folder(path):
    path.mkdir(parents=True, exist_ok=True)

def build_regression_geo(df):

    # Agregación anual por municipio (estructura estable)
    group = df.groupby(["codigo_municipio", "anio"])

    df_geo = group.agg({
        "poblacion_total": "mean",
        "poblacion_menores": "mean",
        "poblacion_adultos": "mean",
        "poblacion_adolescentes": "mean",
        "area_km2": "first",
        "densidad_poblacional": "mean",
        "centros_por_km2": "mean",
        "total_delitos": "sum",
        **{d: "sum" for d in DELITOS}
    }).reset_index()

    # Calcular tasas anuales
    for d in DELITOS:
        df_geo[f"tasa_{d.lower()}"] = df_geo[d] / df_geo["poblacion_total"] * 100000

    return df_geo


def make_regression_geo():
    ensure_folder(OUTPUT_FILE.parent)

    print(f"✔ Cargando GOLD integrado: {INPUT_FILE}")
    df = gpd.read_parquet(INPUT_FILE)

    df_out = build_regression_geo(df)
    df_out.to_parquet(OUTPUT_FILE, index=False)

    print(f"✔ Archivo generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    make_regression_geo()
