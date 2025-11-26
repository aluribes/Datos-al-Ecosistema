"""
04_generate_regression_monthly_dataset.py
==========================================

Genera dataset consolidado para modelos de regresión a nivel mensual.

Entrada:
    data/gold/analytics/gold_analytics.parquet

Salida:
    data/gold/model/regression_monthly_dataset.parquet

Targets disponibles:
    - total_delitos: Total de delitos en el municipio-mes
    - tasa_*: Tasas por 100k habitantes para cada tipo de delito

Este dataset consolida lo que antes eran:
    - regression_total_crimes.parquet
    - regression_per_crime.parquet
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

INPUT_FILE = GOLD_DIR / "analytics" / "gold_analytics.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "regression_monthly_dataset.parquet"

# Columnas a eliminar (no numéricas / no útiles para ML)
DROP_COLS = ["geometry", "municipio", "departamento", "fecha_proper", "anio_mes"]


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def make_regression_monthly_dataset() -> None:
    """
    Genera dataset para regresión mensual.
    
    Incluye todas las features numéricas de gold_analytics:
    - Identificadores: codigo_municipio, codigo_departamento, anio, mes
    - Targets: total_delitos, tasa_* (8 tasas)
    - Features demográficas: poblacion_*, proporciones, densidad
    - Features geográficas: area_km2, centros_por_km2, n_centros_poblados
    - Features temporales: mes_sin, mes_cos, n_festivos, n_dias_laborales
    - Lags: lag_1, lag_3, lag_12
    - Rolling: roll_mean_3, roll_mean_12, roll_std_3, roll_std_12
    - Variaciones: pct_change_1, pct_change_3, pct_change_12
    """
    print("=" * 60)
    print("REGRESSION MONTHLY DATASET")
    print("=" * 60)
    
    print("\nCargando gold_analytics.parquet...")
    df = pd.read_parquet(INPUT_FILE)
    
    # Eliminar columnas no numéricas
    df = df.drop(columns=DROP_COLS, errors="ignore")
    
    # Guardar dataset
    ensure_folder(OUTPUT_FILE.parent)
    df.to_parquet(OUTPUT_FILE, index=False)
    
    # Identificar targets
    tasa_cols = [c for c in df.columns if c.startswith("tasa_")]
    
    print(f"\n✔ Dataset generado: {OUTPUT_FILE}")
    print(f"  - Filas: {len(df):,}")
    print(f"  - Columnas: {len(df.columns)}")
    print(f"  - Targets disponibles:")
    print(f"    - total_delitos")
    for col in tasa_cols:
        print(f"    - {col}")


if __name__ == "__main__":
    make_regression_monthly_dataset()
