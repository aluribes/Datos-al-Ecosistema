# 04_generate_classification_crime_type.py
"""
Clasificación del tipo de delito por evento mensual.
Responde: ¿Qué delito es más probable dado el municipio, mes y contexto?
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"
MODEL_DIR = GOLD_DIR / "model"

POLICIA = GOLD_DIR / "base" / "policia_gold.parquet"
INTEGRADO = GOLD_DIR / "gold_integrado.parquet"
OUTPUT = MODEL_DIR / "classification_crime_type.parquet"

def ensure(p):
    p.mkdir(parents=True, exist_ok=True)

def load():
    return pd.read_parquet(POLICIA), pd.read_parquet(INTEGRADO)

def build(df_pol, df_int):
    # Keys
    df_pol[["anio","mes","codigo_municipio"]] = df_pol[["anio","mes","codigo_municipio"]].astype(int)
    df_int[["anio","mes","codigo_municipio"]] = df_int[["anio","mes","codigo_municipio"]].astype(int)

    # Merge enrich
    df = df_pol.merge(df_int, on=["codigo_municipio","anio","mes"], how="left")

    # Target
    df["delito"] = df["delito"].astype("category")

    # Cyclic month
    df["mes_sin"] = np.sin(2*np.pi*df["mes"]/12)
    df["mes_cos"] = np.cos(2*np.pi*df["mes"]/12)

    return df

def make():
    df_pol, df_int = load()
    df = build(df_pol, df_int)
    ensure(MODEL_DIR)
    df.to_parquet(OUTPUT, index=False)
    print("✔ Archivo generado:", OUTPUT)

if __name__ == "__main__":
    make()
