# 04_generate_classification_profile.py
"""
Clasificación de perfil (edad_persona + genero).
Responde: ¿Qué tipo de persona tiende a ser involucrada en un delito?
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parent.parent
GOLD = BASE / "data" / "gold"
MODEL = GOLD / "model"

POL = GOLD / "base" / "policia_gold.parquet"
INT = GOLD / "gold_integrado.parquet"
OUT = MODEL / "classification_profile.parquet"

def ensure(x): x.mkdir(parents=True, exist_ok=True)

def build(pol, inte):
    for c in ["anio","mes","codigo_municipio"]:
        pol[c] = pol[c].astype(int)
        inte[c] = inte[c].astype(int)

    df = pol.merge(inte, on=["codigo_municipio","anio","mes"], how="left")

    df["perfil"] = (df["genero"].astype(str) + "_" + df["edad_persona"].astype(str)).astype("category")

    df["mes_sin"] = np.sin(2*np.pi*df["mes"]/12)
    df["mes_cos"] = np.cos(2*np.pi*df["mes"]/12)

    return df

def make():
    df = build(pd.read_parquet(POL), pd.read_parquet(INT))
    ensure(MODEL)
    df.to_parquet(OUT, index=False)
    print("✔ Archivo generado:", OUT)

if __name__ == "__main__":
    make()
