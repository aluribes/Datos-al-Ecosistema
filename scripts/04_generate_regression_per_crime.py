"""
Genera dataset para modelos de regresión por tipo de delito.
Entrada:  data/gold/analytics/gold_analytics.parquet
Salida:   data/gold/models/regression_per_crime.parquet

Este dataset incluye:
- Tasas por delito como variables objetivo (y también predictoras cruzadas)
- Variables demográficas
- Variables espaciales
- Lags y rolling stats
- Estacionalidad (sin/cos)
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

INPUT_FILE = GOLD_DIR / "analytics" / "gold_analytics.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "regression_per_crime.parquet"

# Columnas de tasas (se detectan automáticamente)
def get_tasa_columns(df):
    return [c for c in df.columns if c.startswith("tasa_")]

def ensure_folder(path):
    path.mkdir(parents=True, exist_ok=True)

def build_regression_per_crime(df):

    tasa_cols = get_tasa_columns(df)

    # variables predictoras recomendadas
    feature_cols = [
        "codigo_municipio", "anio", "mes",
        "densidad_poblacional", "centros_por_km2",
        "proporcion_menores", "proporcion_adultos",
        "proporcion_adolescentes",
        "mes_sin", "mes_cos",
        "lag_1", "lag_3", "lag_12",
        "roll_mean_3", "roll_mean_12",
        "roll_std_3", "roll_std_12",
        "pct_change_1", "pct_change_3", "pct_change_12",
        "n_dias_semana", "n_fines_de_semana", "n_festivos", "n_dias_laborales"
    ]

    # combinamos predictoras + tasas como salidas
    selected_cols = feature_cols + tasa_cols

    df_out = df[selected_cols].copy()

    return df_out


def make_regression_per_crime():

    ensure_folder(OUTPUT_FILE.parent)

    print(f"✔ Cargando analytics: {INPUT_FILE}")
    df = gpd.read_parquet(INPUT_FILE)

    df_out = build_regression_per_crime(df)
    df_out.to_parquet(OUTPUT_FILE, index=False)

    print(f"✔ Archivo generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    make_regression_per_crime()
