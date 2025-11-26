"""
04_generate_regression_timeseries_dataset.py
=============================================

Genera dataset de serie temporal agregada del departamento completo.

Entrada:
    data/gold/analytics/gold_analytics.parquet

Salida:
    data/gold/model/regression_timeseries_dataset.parquet

Targets disponibles:
    - total_delitos: Total de delitos departamentales por mes
    - tasa_global: Tasa de delitos por 100k habitantes

Uso:
    Modelos de series temporales (ARIMA, Prophet, LSTM) para predecir
    tendencia departamental. Una fila por mes.

Anteriormente: multi_regression.parquet
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

INPUT_FILE = GOLD_DIR / "analytics" / "gold_analytics.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "regression_timeseries_dataset.parquet"


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def build_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega datos a nivel departamental (serie temporal global).
    
    Args:
        df: DataFrame de gold_analytics (nivel municipio-mes)
        
    Returns:
        DataFrame con una fila por mes departamental
    """
    # Agregar por mes (sumar todos los municipios)
    df_global = df.groupby("anio_mes").agg({
        "total_delitos": "sum",
        "poblacion_total": "sum",
    }).reset_index()

    # Convertir a fecha
    df_global["fecha"] = pd.to_datetime(df_global["anio_mes"])
    df_global = df_global.sort_values("fecha")

    # Tasa global por 100k
    df_global["tasa_global"] = (
        df_global["total_delitos"] / df_global["poblacion_total"] * 100000
    )

    # Lags
    df_global["lag_1"] = df_global["total_delitos"].shift(1)
    df_global["lag_3"] = df_global["total_delitos"].shift(3)
    df_global["lag_12"] = df_global["total_delitos"].shift(12)

    # Rolling stats
    df_global["roll_mean_3"] = df_global["total_delitos"].rolling(3).mean()
    df_global["roll_mean_12"] = df_global["total_delitos"].rolling(12).mean()

    # Cambio porcentual
    df_global["pct_change_1"] = df_global["total_delitos"].pct_change(1)
    df_global["pct_change_12"] = df_global["total_delitos"].pct_change(12)

    # Estacionalidad
    df_global["anio"] = df_global["fecha"].dt.year
    df_global["mes"] = df_global["fecha"].dt.month
    df_global["mes_sin"] = np.sin(2 * np.pi * df_global["mes"] / 12)
    df_global["mes_cos"] = np.cos(2 * np.pi * df_global["mes"] / 12)

    return df_global


def make_regression_timeseries_dataset() -> None:
    """
    Genera dataset para regresión de serie temporal.
    """
    print("=" * 60)
    print("REGRESSION TIMESERIES DATASET")
    print("=" * 60)
    
    print("\nCargando gold_analytics.parquet...")
    df = gpd.read_parquet(INPUT_FILE)
    print(f"  - Registros municipio-mes: {len(df):,}")
    
    print("\nAgregando a serie temporal departamental...")
    df_out = build_timeseries(df)
    
    # Estadísticas
    print(f"\n  Rango de fechas: {df_out['fecha'].min()} a {df_out['fecha'].max()}")
    print(f"  Meses totales: {len(df_out)}")
    
    # Guardar dataset
    ensure_folder(OUTPUT_FILE.parent)
    df_out.to_parquet(OUTPUT_FILE, index=False)
    
    print(f"\n✔ Dataset generado: {OUTPUT_FILE}")
    print(f"  - Filas: {len(df_out):,}")
    print(f"  - Columnas: {list(df_out.columns)}")
    print(f"  - Targets: total_delitos, tasa_global")


if __name__ == "__main__":
    make_regression_timeseries_dataset()
