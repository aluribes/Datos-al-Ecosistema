from pathlib import Path

import pandas as pd

# === CONFIGURACIÓN ===
BASE_DIR = Path(__file__).resolve().parent
GOLD_ROOT = BASE_DIR / "data" / "gold"

# Rutas de entrada/salida
GOLD_INPUT = GOLD_ROOT / "gold_integrado.parquet"
MODEL_OUTPUT = GOLD_ROOT / "model" / "df_modelo.parquet"


def ensure_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save(df: pd.DataFrame, path: Path) -> None:
    ensure_folder(path.parent)
    df.to_parquet(path, index=False)


# Load GOLD Integrado
def load_gold_integrado() -> pd.DataFrame:
    print(f"✔ Cargando GOLD integrado: {GOLD_INPUT}")
    return pd.read_parquet(GOLD_INPUT)


# Seleccionar dataset para modelado
def build_model_dataset(df: pd.DataFrame) -> pd.DataFrame:

    print("➤ Construyendo dataset para el modelo predictivo…")

    delitos_cols = [c for c in df.columns if c.isupper()]  # delitos pivotados

    cols_modelo = [
        "codigo_municipio",
        "anio",
        "mes",
        "total_delitos",
        "poblacion_total",
        "densidad_poblacional",
        "proporcion_menores",
        "proporcion_adultos",
        "proporcion_adolescentes",
        "centros_por_km2",
        "area_km2",
        "n_centros_poblados",
        "trimestre",
    ] + delitos_cols

    df_modelo = df[cols_modelo].dropna(subset=["total_delitos"])
    df_modelo = df_modelo.sort_values(["codigo_municipio", "anio", "mes"])

    return df_modelo


# Ejecucion para generar dataset de modelado
def make_model_dataset() -> None:

    df = load_gold_integrado()
    df_modelo = build_model_dataset(df)

    save(df_modelo, MODEL_OUTPUT)
    print("✔ df_modelo.parquet generado.")


if __name__ == "__main__":
    make_model_dataset()
