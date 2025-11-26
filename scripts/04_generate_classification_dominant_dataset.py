"""
04_generate_classification_dominant_dataset.py
===============================================

Genera dataset consolidado para identificar delito/arma dominante por municipio-mes.

Entrada:
    data/gold/base/policia_gold.parquet

Salida:
    data/gold/model/classification_dominant_dataset.parquet

Targets disponibles:
    - delito_dominante: Tipo de delito más frecuente en el municipio-mes
    - arma_dominante: Tipo de arma/medio más usado en el municipio-mes
    - count_delito: Cantidad de eventos del delito dominante
    - count_arma: Cantidad de eventos del arma dominante

Este dataset consolida lo que antes eran:
    - classification_dominant_crime.parquet
    - classification_dominant_weapon.parquet
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

POLICIA_FILE = GOLD_DIR / "base" / "policia_gold.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "classification_dominant_dataset.parquet"


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def get_dominant(df: pd.DataFrame, group_cols: list, target_col: str) -> pd.DataFrame:
    """
    Obtiene el valor dominante (más frecuente) de una columna por grupo.
    
    Args:
        df: DataFrame de origen
        group_cols: Columnas para agrupar
        target_col: Columna de la cual obtener el valor dominante
        
    Returns:
        DataFrame con el valor dominante y su conteo
    """
    counts = (
        df.groupby(group_cols + [target_col])
        .size()
        .reset_index(name="count")
    )
    
    # Obtener el índice del máximo por grupo
    idx = counts.groupby(group_cols)["count"].idxmax()
    
    return counts.loc[idx].reset_index(drop=True)


def make_classification_dominant_dataset() -> None:
    """
    Genera dataset consolidado de delito/arma dominante por municipio-mes.
    
    Targets:
        - delito_dominante: Tipo de delito más frecuente
        - arma_dominante: Tipo de arma/medio más usado
    """
    print("=" * 60)
    print("CLASSIFICATION DOMINANT DATASET")
    print("=" * 60)
    
    print("\nCargando policia_gold.parquet...")
    df = pd.read_parquet(POLICIA_FILE)
    print(f"  - Eventos: {len(df):,}")
    
    group_cols = ["codigo_municipio", "anio", "mes"]
    
    # Delito dominante
    print("\nCalculando delito dominante por municipio-mes...")
    df_delito = get_dominant(df, group_cols, "delito")
    df_delito = df_delito.rename(columns={
        "delito": "delito_dominante",
        "count": "count_delito"
    })
    
    # Arma dominante
    print("Calculando arma dominante por municipio-mes...")
    df_arma = get_dominant(df, group_cols, "armas_medios")
    df_arma = df_arma.rename(columns={
        "armas_medios": "arma_dominante",
        "count": "count_arma"
    })
    
    # Fusionar ambos
    df_out = df_delito.merge(
        df_arma,
        on=group_cols,
        how="outer"
    )
    
    # Convertir targets a categóricos
    df_out["delito_dominante"] = df_out["delito_dominante"].astype("category")
    df_out["arma_dominante"] = df_out["arma_dominante"].astype("category")
    
    # Mostrar estadísticas
    print(f"\n  Municipios-mes únicos: {len(df_out):,}")
    print(f"\n  Target: delito_dominante")
    print(f"    - Categorías: {df_out['delito_dominante'].nunique()}")
    
    print(f"\n  Target: arma_dominante")
    print(f"    - Categorías: {df_out['arma_dominante'].nunique()}")
    
    # Guardar dataset
    ensure_folder(OUTPUT_FILE.parent)
    df_out.to_parquet(OUTPUT_FILE, index=False)
    
    print(f"\n✔ Dataset generado: {OUTPUT_FILE}")
    print(f"  - Filas: {len(df_out):,}")
    print(f"  - Columnas: {list(df_out.columns)}")
    print(f"  - Targets: delito_dominante, arma_dominante")


if __name__ == "__main__":
    make_classification_dominant_dataset()
