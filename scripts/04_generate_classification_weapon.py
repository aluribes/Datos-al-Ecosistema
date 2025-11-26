# 04_generate_classification_weapon_type.py
"""
Clasificación del tipo de arma usada en cada evento.
Responde: ¿Qué arma es más probable dado el delito y el contexto municipal?
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD = BASE_DIR / "data" / "gold"
MODEL = GOLD / "model"

POL = GOLD / "base" / "policia_gold.parquet"
INT = GOLD / "gold_integrado.parquet"
OUT = MODEL / "classification_weapon_type.parquet"

def ensure(p): p.mkdir(parents=True, exist_ok=True)

def build(pol, inte):
    pol[["anio","mes","codigo_municipio"]] = pol[["anio","mes","codigo_municipio"]].astype(int)
    inte[["anio","mes","codigo_municipio"]] = inte[["anio","mes","codigo_municipio"]].astype(int)

    df = pol.merge(inte, on=["codigo_municipio","anio","mes"], how="left")
    df["armas_medios"] = df["armas_medios"].astype("category")

    df["mes_sin"] = np.sin(2*np.pi*df["mes"]/12)
    df["mes_cos"] = np.cos(2*np.pi*df["mes"]/12)

    return df

def make():
    pol = pd.read_parquet(POL)
    inte = pd.read_parquet(INT)
    df = build(pol, inte)
    ensure(MODEL)
    df.to_parquet(OUT, index=False)
    print("✔ Archivo generado:", OUT)

if __name__ == "__main__":
    make()
