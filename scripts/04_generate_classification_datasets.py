"""
04_generate_classification_datasets.py
======================================

Genera datasets para modelos de clasificación:
    1. nivel_riesgo: BAJO / MEDIO / ALTO basado en percentiles de total_delitos
    2. incremento_delitos: 0 / 1 si aumentaron vs mes anterior

Entrada:
    data/gold/analytics/gold_analytics.parquet
Salida:
    data/gold/model/classification_riesgo_dataset.parquet
    data/gold/model/classification_incremento_dataset.parquet
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
ANALYTICS = BASE_DIR / "data" / "gold" / "analytics" / "gold_analytics.parquet"
OUT_RIESGO = BASE_DIR / "data" / "gold" / "model" / "classification_riesgo_dataset.parquet"
OUT_INCREMENTO = BASE_DIR / "data" / "gold" / "model" / "classification_incremento_dataset.parquet"

# Columnas a eliminar (no numéricas / no útiles para ML)
DROP_COLS = ["geometry", "municipio", "departamento", "fecha_proper", "anio_mes"]


def ensure_folder(p: Path) -> None:
    """Crea directorio si no existe."""
    p.mkdir(parents=True, exist_ok=True)


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
    return (df["pct_change_1"] > 0).astype(int)


def make_classification_riesgo_dataset() -> None:
    """
    Genera dataset para clasificación de nivel de riesgo (multiclase).
    
    Target: nivel_riesgo (BAJO/MEDIO/ALTO)
    """
    print("=" * 60)
    print("DATASET 1: Clasificación por Nivel de Riesgo")
    print("=" * 60)
    
    print("\nCargando gold_analytics.parquet...")
    df = pd.read_parquet(ANALYTICS)
    
    # Crear variable target
    print("Creando variable target: nivel_riesgo...")
    df["nivel_riesgo"] = create_nivel_riesgo(df["total_delitos"])
    
    # Mostrar distribución y percentiles
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
    
    # Eliminar columnas no numéricas
    df = df.drop(columns=DROP_COLS, errors="ignore")
    
    # Guardar dataset
    ensure_folder(OUT_RIESGO.parent)
    df.to_parquet(OUT_RIESGO, index=False)
    
    print(f"\n✔ Dataset generado: {OUT_RIESGO}")
    print(f"  - Filas: {len(df):,}")
    print(f"  - Columnas: {len(df.columns)}")


def make_classification_incremento_dataset() -> None:
    """
    Genera dataset para clasificación binaria de incremento de delitos.
    
    Target: incremento_delitos (0/1)
    """
    print("\n" + "=" * 60)
    print("DATASET 2: Clasificación Binaria (Incremento)")
    print("=" * 60)
    
    print("\nCargando gold_analytics.parquet...")
    df = pd.read_parquet(ANALYTICS)
    
    # Crear variable target
    print("Creando variable target: incremento_delitos...")
    df["incremento_delitos"] = create_incremento_delitos(df)
    
    # Eliminar filas donde no se puede calcular el incremento (primer mes)
    rows_before = len(df)
    df = df.dropna(subset=["pct_change_1"])
    rows_after = len(df)
    print(f"  - Filas eliminadas (sin mes anterior): {rows_before - rows_after:,}")
    
    # Mostrar distribución
    print("\n  Distribución de incremento_delitos:")
    for clase in [0, 1]:
        count = (df["incremento_delitos"] == clase).sum()
        pct = (df["incremento_delitos"] == clase).mean()
        label = "Sin incremento" if clase == 0 else "Con incremento"
        print(f"    - {clase} ({label}): {count:,} ({pct:.1%})")
    
    # Eliminar columnas no numéricas
    df = df.drop(columns=DROP_COLS, errors="ignore")
    
    # Guardar dataset
    ensure_folder(OUT_INCREMENTO.parent)
    df.to_parquet(OUT_INCREMENTO, index=False)
    
    print(f"\n✔ Dataset generado: {OUT_INCREMENTO}")
    print(f"  - Filas: {len(df):,}")
    print(f"  - Columnas: {len(df.columns)}")


def main() -> None:
    """Genera ambos datasets de clasificación."""
    make_classification_riesgo_dataset()
    make_classification_incremento_dataset()
    print("\n" + "=" * 60)
    print("✔ Ambos datasets de clasificación generados exitosamente")
    print("=" * 60)


if __name__ == "__main__":
    main()
