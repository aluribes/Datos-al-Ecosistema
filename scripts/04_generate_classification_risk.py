# 04_generate_classification_risk_monthly.py
"""
Clasificación del nivel de riesgo mensual.
Categorías: bajo, medio, alto según percentiles de total_delitos.
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parent.parent
GOLD = BASE / "data" / "gold"
MODEL = GOLD / "model"

INT = GOLD / "gold_integrado.parquet"
OUT = MODEL / "classification_risk_monthly.parquet"

def ensure(x): x.mkdir(parents=True, exist_ok=True)

def build(df):
    df = df.copy()

    # Calcular niveles de riesgo
    df["riesgo"] = pd.qcut(df["total_delitos"], q=3, labels=["bajo","medio","alto"])

    df["mes_sin"] = np.sin(2*np.pi*df["mes"]/12)
    df["mes_cos"] = np.cos(2*np.pi*df["mes"]/12)

    return df

def make():
    df = pd.read_parquet(INT)
    out = build(df)
    ensure(MODEL)
    out.to_parquet(OUT, index=False)
    print("✔ Archivo generado:", OUT)

if __name__ == "__main__":
    make()
