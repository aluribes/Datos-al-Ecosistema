from pathlib import Path

import pandas as pd
import geopandas as gpd

# === CONFIGURACIÓN ===
BASE_DIR = Path(__file__).resolve().parent
GOLD_ROOT = BASE_DIR / "data" / "gold"

# Rutas de entrada/salida
GOLD_INPUT = GOLD_ROOT / "gold_integrado.parquet"
ANALYTICS_OUTPUT = GOLD_ROOT / "analytics" / "gold_analytics.parquet"

# Tipos de delitos para cálculo de tasas
DELITOS_BASE = [
    "ABIGEATO", "HURTOS", "LESIONES",
    "VIOLENCIA INTRAFAMILIAR", "AMENAZAS",
    "DELITOS SEXUALES", "EXTORSION", "HOMICIDIOS"
]


def ensure_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def save(df, path: Path):
    ensure_folder(path.parent)
    df.to_parquet(path, index=False)


# Load GOLD Integrado
def load_gold_integrado():
    print(f"✔ Cargando GOLD integrado: {GOLD_INPUT}")
    return gpd.read_parquet(GOLD_INPUT)


# Generar indicadores analíticos
def build_analytics(df):

    print("➤ Calculando tasas de delito por 100.000 habitantes…")

    for col in DELITOS_BASE:
        if col in df.columns:
            df[f"tasa_{col.lower().replace(' ', '_')}"] = (
                df[col] / df["poblacion_total"] * 100000
            )

    print("➤ Calculando indicadores espaciales y demográficos…")

    df["densidad_poblacional"] = df["poblacion_total"] / df["area_km2"]
    df["centros_por_km2"] = df["n_centros_poblados"] / df["area_km2"]

    df["proporcion_menores"] = df["poblacion_menores"] / df["poblacion_total"]
    df["proporcion_adultos"] = df["poblacion_adultos"] / df["poblacion_total"]
    df["proporcion_adolescentes"] = df["poblacion_adolescentes"] / df["poblacion_total"]

    return df



# Ejecucion para generar analiticos
def make_analytics():

    df = load_gold_integrado()
    df_analytics = build_analytics(df)

    save(df_analytics, ANALYTICS_OUTPUT)
    print("✔ gold_analytics.parquet generado.")


if __name__ == "__main__":
    make_analytics()
