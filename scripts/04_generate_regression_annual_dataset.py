"""
04_generate_regression_annual_dataset.py
=========================================

Genera dataset agregado a nivel anual para análisis espacial y regresión geográfica.

Entrada:
    data/gold/gold_integrado.parquet

Salida:
    data/gold/model/regression_annual_dataset.parquet

Targets disponibles:
    - total_delitos: Total de delitos anuales por municipio
    - tasa_*: Tasas anuales por 100k habitantes para cada tipo de delito

Uso:
    Análisis espacial y comparativas entre municipios a nivel anual.
    Útil para modelos que no requieren granularidad mensual.

Anteriormente: regression_geo.parquet
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

INPUT_FILE = GOLD_DIR / "gold_integrado.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "regression_annual_dataset.parquet"

DELITOS = [
    "ABIGEATO", "HURTOS", "LESIONES", "VIOLENCIA INTRAFAMILIAR",
    "AMENAZAS", "DELITOS SEXUALES", "EXTORSION", "HOMICIDIOS"
]


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def build_regression_annual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega datos a nivel anual por municipio.
    
    Args:
        df: DataFrame de gold_integrado (nivel mensual)
        
    Returns:
        DataFrame agregado a nivel anual con tasas calculadas
    """
    # Agregación anual por municipio
    group = df.groupby(["codigo_municipio", "anio"])

    df_annual = group.agg({
        "poblacion_total": "mean",
        "poblacion_menores": "mean",
        "poblacion_adultos": "mean",
        "poblacion_adolescentes": "mean",
        "area_km2": "first",
        "densidad_poblacional": "mean",
        "centros_por_km2": "mean",
        "total_delitos": "sum",
        **{d: "sum" for d in DELITOS}
    }).reset_index()

    # Calcular tasas anuales por 100k habitantes
    for d in DELITOS:
        df_annual[f"tasa_{d.lower()}"] = (
            df_annual[d] / df_annual["poblacion_total"] * 100000
        )

    return df_annual


def make_regression_annual_dataset() -> None:
    """
    Genera dataset para regresión anual/geográfica.
    """
    print("=" * 60)
    print("REGRESSION ANNUAL DATASET")
    print("=" * 60)
    
    print("\nCargando gold_integrado.parquet...")
    df = gpd.read_parquet(INPUT_FILE)
    print(f"  - Registros mensuales: {len(df):,}")
    
    print("\nAgregando a nivel anual...")
    df_out = build_regression_annual(df)
    
    # Estadísticas
    print(f"\n  Municipios únicos: {df_out['codigo_municipio'].nunique()}")
    print(f"  Años: {sorted(df_out['anio'].unique())}")
    
    # Guardar dataset
    ensure_folder(OUTPUT_FILE.parent)
    df_out.to_parquet(OUTPUT_FILE, index=False)
    
    # Identificar targets
    tasa_cols = [c for c in df_out.columns if c.startswith("tasa_")]
    
    print(f"\n✔ Dataset generado: {OUTPUT_FILE}")
    print(f"  - Filas: {len(df_out):,}")
    print(f"  - Columnas: {len(df_out.columns)}")
    print(f"  - Targets: total_delitos, {len(tasa_cols)} tasas")


if __name__ == "__main__":
    make_regression_annual_dataset()
