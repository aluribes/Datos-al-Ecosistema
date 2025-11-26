"""
04_generate_classification_monthly_dataset.py
==============================================

Genera dataset consolidado para modelos de clasificación a nivel mensual.

Entrada:
    data/gold/analytics/gold_analytics.parquet

Salida:
    data/gold/model/classification_monthly_dataset.parquet

Targets disponibles:
    - nivel_riesgo: BAJO / MEDIO / ALTO (basado en percentiles de total_delitos)
    - incremento_delitos: 0 / 1 (si aumentaron vs mes anterior)

Este dataset consolida lo que antes eran:
    - classification_riesgo_dataset.parquet
    - classification_incremento_dataset.parquet
    - classification_risk_monthly.parquet (eliminado por redundancia)
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

INPUT_FILE = GOLD_DIR / "analytics" / "gold_analytics.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "classification_monthly_dataset.parquet"

# Columnas a eliminar (no numéricas / no útiles para ML)
DROP_COLS = ["geometry", "municipio", "departamento", "fecha_proper", "anio_mes"]


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def create_nivel_riesgo(series: pd.Series) -> pd.Series:
    """
    Clasifica total_delitos en niveles de riesgo basado en percentiles.
    
    - BAJO:  <= percentil 33
    - MEDIO: > percentil 33 y <= percentil 66
    - ALTO:  > percentil 66
    
    Args:
        series: Serie con valores de total_delitos
        
    Returns:
        Serie categórica con niveles BAJO/MEDIO/ALTO
    """
    p33 = series.quantile(0.33)
    p66 = series.quantile(0.66)
    
    conditions = [
        series <= p33,
        (series > p33) & (series <= p66),
        series > p66
    ]
    choices = ["BAJO", "MEDIO", "ALTO"]
    
    return pd.Series(
        np.select(conditions, choices, default="MEDIO"),
        index=series.index,
        dtype="category"
    )


def create_incremento_delitos(df: pd.DataFrame) -> pd.Series:
    """
    Crea variable binaria indicando si los delitos aumentaron vs mes anterior.
    
    Usa pct_change_1 (ya calculado en gold_analytics) para determinar:
        - 1: Si pct_change_1 > 0 (hubo incremento)
        - 0: Si pct_change_1 <= 0 (se mantuvo o disminuyó)
    
    Args:
        df: DataFrame con columna pct_change_1
        
    Returns:
        Serie binaria (0/1) indicando incremento
    """
    return (df["pct_change_1"] > 0).astype("Int64")


def make_classification_monthly_dataset() -> None:
    """
    Genera dataset consolidado para clasificación mensual.
    
    Targets:
        - nivel_riesgo (BAJO/MEDIO/ALTO): Clasificación multiclase
        - incremento_delitos (0/1): Clasificación binaria
    """
    print("=" * 60)
    print("CLASSIFICATION MONTHLY DATASET")
    print("=" * 60)
    
    print("\nCargando gold_analytics.parquet...")
    df = pd.read_parquet(INPUT_FILE)
    
    # Crear target: nivel_riesgo
    print("Creando target: nivel_riesgo...")
    df["nivel_riesgo"] = create_nivel_riesgo(df["total_delitos"])
    
    # Mostrar distribución de nivel_riesgo
    p33 = df["total_delitos"].quantile(0.33)
    p66 = df["total_delitos"].quantile(0.66)
    print(f"\n  Percentiles de total_delitos:")
    print(f"    - P33: {p33:.0f}")
    print(f"    - P66: {p66:.0f}")
    
    print("\n  Distribución de nivel_riesgo:")
    for nivel in ["BAJO", "MEDIO", "ALTO"]:
        count = (df["nivel_riesgo"] == nivel).sum()
        pct = (df["nivel_riesgo"] == nivel).mean()
        print(f"    - {nivel}: {count:,} ({pct:.1%})")
    
    # Crear target: incremento_delitos
    print("\nCreando target: incremento_delitos...")
    df["incremento_delitos"] = create_incremento_delitos(df)
    
    # Mostrar distribución de incremento_delitos
    print("\n  Distribución de incremento_delitos:")
    for clase in [0, 1]:
        count = (df["incremento_delitos"] == clase).sum()
        pct = (df["incremento_delitos"] == clase).mean()
        label = "Sin incremento" if clase == 0 else "Con incremento"
        print(f"    - {clase} ({label}): {count:,} ({pct:.1%})")
    
    # Contar NaN en incremento (primer mes de cada municipio)
    nan_count = df["incremento_delitos"].isna().sum()
    print(f"    - NaN (primer mes): {nan_count:,}")
    
    # Eliminar columnas no numéricas
    df = df.drop(columns=DROP_COLS, errors="ignore")
    
    # Guardar dataset
    ensure_folder(OUTPUT_FILE.parent)
    df.to_parquet(OUTPUT_FILE, index=False)
    
    print(f"\n✔ Dataset generado: {OUTPUT_FILE}")
    print(f"  - Filas: {len(df):,}")
    print(f"  - Columnas: {len(df.columns)}")
    print(f"  - Targets: nivel_riesgo, incremento_delitos")


if __name__ == "__main__":
    make_classification_monthly_dataset()
