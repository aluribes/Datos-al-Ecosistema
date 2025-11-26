"""
Genera dataset limpio para modelos de regresión:
    - Predicción de total_delitos
    - Predicción de tasas

Entrada:
    data/gold/analytics/gold_analytics.parquet
Salida:
    data/gold/model/regression_total_crimes.parquet
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
ANALYTICS = BASE_DIR / "data" / "gold" / "analytics" / "gold_analytics.parquet"
OUT = BASE_DIR / "data" / "gold" / "model" / "regression_total_crimes.parquet"


def ensure_folder(p):
    p.mkdir(parents=True, exist_ok=True)


def make_regression_dataset():
    df = pd.read_parquet(ANALYTICS)

    # eliminar columnas no numéricas / no útiles
    drop_cols = ["geometry", "municipio", "departamento", "fecha_proper", "anio_mes"]
    df = df.drop(columns=drop_cols, errors="ignore")

    ensure_folder(OUT.parent)
    df.to_parquet(OUT, index=False)

    print(f"✔ Dataset de regresión generado: {OUT}")


if __name__ == "__main__":
    make_regression_dataset()
