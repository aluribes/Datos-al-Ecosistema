"""
04_generate_classification_data.py
==================================

Genera dataset mensual para clasificación:
    - etiquetas: tipo de delito o tipo de arma
    - variables: conteos agregados por municipio/mes

Entrada:
    - data/gold/base/policia_gold.parquet (datos por evento)
    - data/gold/gold_integrado.parquet (contexto demográfico y delictivo mensual)

Salida:
    - data/gold/model/classification_weapons.parquet

Incluye:
    ✔ Datos detallados por evento: delito, arma, género, edad, festivos, etc.
    ✔ Contexto municipal mensual: población, densidad, proporciones, tasas, etc.
    ✔ Indicadores temporales: mes, trimestre, codificación cíclica.
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"
MODEL_DIR = GOLD_DIR / "model"

# INPUT FILES
POLICIA_FILE = GOLD_DIR / "base" / "policia_gold.parquet"
INTEGRADO_FILE = GOLD_DIR / "gold_integrado.parquet"

# OUTPUT
OUTPUT_FILE = MODEL_DIR / "classification_weapons.parquet"


def ensure_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def save(df: pd.DataFrame, path: Path):
    ensure_folder(path.parent)
    df.to_parquet(path, index=False)


# Cargar fuentes
def load_sources():
    print("✔ Cargando policia_gold.parquet…")
    df_pol = pd.read_parquet(POLICIA_FILE)

    print("✔ Cargando gold_integrado.parquet…")
    df_int = pd.read_parquet(INTEGRADO_FILE)

    print("✔ Archivos cargados.")
    return df_pol, df_int


# Generar features
def build_classification_dataset(df_pol, df_int):

    # 1) Unificar claves
    df_pol["anio"] = df_pol["anio"].astype(int)
    df_pol["mes"] = df_pol["mes"].astype(int)
    df_pol["codigo_municipio"] = df_pol["codigo_municipio"].astype(int)

    df_int["anio"] = df_int["anio"].astype(int)
    df_int["mes"] = df_int["mes"].astype(int)
    df_int["codigo_municipio"] = df_int["codigo_municipio"].astype(int)

    # 2) Merge (LEFT) para enriquecer cada delito con su contexto mensual
    print("✔ Enlazando policia_gold con gold_integrado (merge)…")

    df = df_pol.merge(
        df_int,
        on=["codigo_municipio", "anio", "mes"],
        how="left",
        suffixes=("", "_ctx")
    )

    # 3) Crear codificación cíclica del mes
    print("✔ Agregando codificación cíclica del mes…")
    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)

    # 4) Variables objetivo 
    # Y1 = tipo de delito
    # Y2 = arma usada

    df["delito"] = df["delito"].astype("category")
    df["armas_medios"] = df["armas_medios"].astype("category")

    print("✔ Dataset de clasificación construido.")

    return df


# Ejecución
def make_classification_dataset():
    df_pol, df_int = load_sources()
    df_class = build_classification_dataset(df_pol, df_int)

    save(df_class, OUTPUT_FILE)
    print(f"✔ Archivo generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    make_classification_dataset()
