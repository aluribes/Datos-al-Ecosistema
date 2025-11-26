"""
Genera dataset temporal agregado (serie global del departamento).
Entrada:  data/gold/analytics/gold_analytics.parquet
Salida:   data/gold/model/multi_regression.parquet

Incluye:
- total de delitos departamental por mes
- tasas departamentales agregadas
- rolling, lags y pct_change sobre la serie global
- estacionalidad (sin/cos)
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

INPUT_FILE = GOLD_DIR / "analytics" / "gold_analytics.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "multi_regression.parquet"

def ensure_folder(path):
    path.mkdir(parents=True, exist_ok=True)

def build_multi_regression(df):

    df_global = df.groupby("anio_mes").agg({
        "total_delitos": "sum",
        "poblacion_total": "sum",
    }).reset_index()

    df_global["fecha"] = pd.to_datetime(df_global["anio_mes"])

    df_global = df_global.sort_values("fecha")

    # Tasas globales
    df_global["tasa_global"] = df_global["total_delitos"] / df_global["poblacion_total"] * 100000

    # Lags
    df_global["lag_1"] = df_global["total_delitos"].shift(1)
    df_global["lag_3"] = df_global["total_delitos"].shift(3)
    df_global["lag_12"] = df_global["total_delitos"].shift(12)

    # Rolling
    df_global["roll_3"] = df_global["total_delitos"].rolling(3).mean()
    df_global["roll_12"] = df_global["total_delitos"].rolling(12).mean()

    # Cambio porcentual
    df_global["pct_change_1"] = df_global["total_delitos"].pct_change(1)
    df_global["pct_change_12"] = df_global["total_delitos"].pct_change(12)

    # Estacionalidad
    df_global["mes"] = df_global["fecha"].dt.month
    df_global["mes_sin"] = np.sin(2 * np.pi * df_global["mes"] / 12)
    df_global["mes_cos"] = np.cos(2 * np.pi * df_global["mes"] / 12)

    return df_global


def make_multi_regression():

    print(f"✔ Cargando analytics: {INPUT_FILE}")
    df = gpd.read_parquet(INPUT_FILE)

    ensure_folder(OUTPUT_FILE.parent)

    df_out = build_multi_regression(df)
    df_out.to_parquet(OUTPUT_FILE, index=False)

    print(f"✔ Archivo generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    make_multi_regression()
