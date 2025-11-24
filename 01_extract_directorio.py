#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ETL para el dataset:
Directorio de cuadrantes de Policía - Santander (ya2b-dnfa)
Fuente: https://www.datos.gov.co/resource/ya2b-dnfa.json
"""

import os
import pandas as pd
from sodapy import Socrata
from datetime import datetime

# -------------------------------------------------------
# CONFIGURACIÓN GENERAL
# -------------------------------------------------------

SOCRATA_DOMAIN = "www.datos.gov.co"
SOCRATA_TOKEN = None  
DATASET_ID = "ya2b-dnfa"

BASE_DIR = "data"
BASE = "directorio_cuadrantes_santander"
BRONZE_DIR = f"{BASE_DIR}/bronze/{BASE}"
SILVER_DIR = f"{BASE_DIR}/silver/{BASE}"
GOLD_DIR   = f"{BASE_DIR}/gold/{BASE}"

os.makedirs(BRONZE_DIR, exist_ok=True)
os.makedirs(SILVER_DIR, exist_ok=True)
os.makedirs(GOLD_DIR, exist_ok=True)

# Cliente Socrata
client = Socrata(SOCRATA_DOMAIN, SOCRATA_TOKEN)

# -------------------------------------------------------
# 1. EXTRACCIÓN (BRONZE)
# -------------------------------------------------------

def extract_data():
    print("Extrayendo datos desde datos.gov.co ...")

    try:
        results = client.get(DATASET_ID, limit=50000)
        df = pd.DataFrame.from_records(results)

        # Archivo fijo (siempre se sobrescribe)
        raw_path = f"{BRONZE_DIR}/cuadrantes_santander_raw.json"
        df.to_json(raw_path, orient="records", force_ascii=False)

        print(f"Datos crudos guardados en: {raw_path}")
        return df

    except Exception as e:
        print(f"Error en extracción: {e}")
        return None
# -------------------------------------------------------
# 2. TRANSFORMACIÓN (SILVER)
# -------------------------------------------------------

def clean_dataframe(df):
    print("Limpiando y transformando datos ...")

    # Normalizar nombres de columna
    df.columns = (
        df.columns
        .str.lower()
        .str.replace(" ", "_")
        .str.normalize("NFKD")
        .str.encode("ascii", "ignore")
        .str.decode("utf-8")
    )

    # Convertir tipos (si existen)
    numeric_cols = ["cuadrante", "telefono"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Quitar duplicados
    df = df.drop_duplicates()

    # Quitar columnas 100% vacías
    df = df.dropna(axis=1, how="all")

    # Reemplazar strings vacíos con NaN
    df = df.replace("", pd.NA)

    print("Transformación terminada.")
    return df


def save_silver(df):
    # Archivos fijos que se sobrescriben
    path_json = f"{SILVER_DIR}/cuadrantes_silver.json"
    path_csv  = f"{SILVER_DIR}/cuadrantes_silver.csv"

    df.to_json(path_json, orient="records", force_ascii=False)
    df.to_csv(path_csv, index=False)

    print(f"Datos limpios guardados en:\n  {path_json}\n  {path_csv}")


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

def main():
    df_raw = extract_data()
    if df_raw is None:
        return

    df_clean = clean_dataframe(df_raw)
    save_silver(df_clean)


if __name__ == "__main__":
    main()
