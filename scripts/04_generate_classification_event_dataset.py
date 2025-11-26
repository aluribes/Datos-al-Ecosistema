"""
04_generate_classification_event_dataset.py
============================================

Genera dataset consolidado para modelos de clasificación a nivel de evento.
Cada fila representa un delito individual enriquecido con contexto municipal.

Entrada:
    data/gold/base/policia_gold.parquet (eventos individuales)
    data/gold/gold_integrado.parquet (contexto mensual por municipio)

Salida:
    data/gold/model/classification_event_dataset.parquet

Targets disponibles:
    - delito: Tipo de delito (8 categorías)
    - armas_medios: Tipo de arma/medio usado (47 categorías)
    - perfil: Combinación género + edad (9 categorías)

Este dataset consolida lo que antes eran:
    - classification_crime_type.parquet
    - classification_weapon_type.parquet
    - classification_profile.parquet
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

POLICIA_FILE = GOLD_DIR / "base" / "policia_gold.parquet"
INTEGRADO_FILE = GOLD_DIR / "gold_integrado.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "classification_event_dataset.parquet"


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def build_event_dataset(df_pol: pd.DataFrame, df_int: pd.DataFrame) -> pd.DataFrame:
    """
    Construye dataset de eventos enriquecido con contexto municipal.
    
    Args:
        df_pol: DataFrame de policia_gold (cada fila = un delito)
        df_int: DataFrame de gold_integrado (contexto mensual por municipio)
        
    Returns:
        DataFrame enriquecido con targets categóricos
    """
    # Asegurar tipos de claves para el merge
    for col in ["anio", "mes", "codigo_municipio"]:
        df_pol[col] = df_pol[col].astype(int)
        df_int[col] = df_int[col].astype(int)
    
    # Merge para enriquecer cada delito con su contexto mensual
    df = df_pol.merge(
        df_int,
        on=["codigo_municipio", "anio", "mes"],
        how="left",
        suffixes=("", "_ctx")
    )
    
    # Codificación cíclica del mes
    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)
    
    # Target 1: delito (categórico)
    df["delito"] = df["delito"].astype("category")
    
    # Target 2: armas_medios (categórico)
    df["armas_medios"] = df["armas_medios"].astype("category")
    
    # Target 3: perfil (género + edad)
    df["perfil"] = (
        df["genero"].astype(str) + "_" + df["edad_persona"].astype(str)
    ).astype("category")
    
    return df


def make_classification_event_dataset() -> None:
    """
    Genera dataset consolidado para clasificación de eventos.
    
    Targets:
        - delito: Tipo de delito
        - armas_medios: Tipo de arma/medio
        - perfil: Género + edad de la persona
    """
    print("=" * 60)
    print("CLASSIFICATION EVENT DATASET")
    print("=" * 60)
    
    print("\nCargando policia_gold.parquet...")
    df_pol = pd.read_parquet(POLICIA_FILE)
    print(f"  - Eventos: {len(df_pol):,}")
    
    print("\nCargando gold_integrado.parquet...")
    df_int = pd.read_parquet(INTEGRADO_FILE)
    print(f"  - Registros mensuales: {len(df_int):,}")
    
    print("\nConstruyendo dataset enriquecido...")
    df = build_event_dataset(df_pol, df_int)
    
    # Mostrar estadísticas de targets
    print("\n  Target: delito")
    print(f"    - Categorías: {df['delito'].nunique()}")
    print(f"    - Valores: {list(df['delito'].cat.categories)}")
    
    print("\n  Target: armas_medios")
    print(f"    - Categorías: {df['armas_medios'].nunique()}")
    
    print("\n  Target: perfil")
    print(f"    - Categorías: {df['perfil'].nunique()}")
    print(f"    - Valores: {list(df['perfil'].cat.categories)}")
    
    # Guardar dataset
    ensure_folder(OUTPUT_FILE.parent)
    df.to_parquet(OUTPUT_FILE, index=False)
    
    print(f"\n✔ Dataset generado: {OUTPUT_FILE}")
    print(f"  - Filas: {len(df):,}")
    print(f"  - Columnas: {len(df.columns)}")
    print(f"  - Targets: delito, armas_medios, perfil")


if __name__ == "__main__":
    make_classification_event_dataset()
