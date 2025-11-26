"""
04_generate_clustering_geo_dataset.py
======================================

Genera dataset con clusters geográficos de municipios basado en perfil delictivo.

Entrada:
    data/gold/gold_integrado.parquet

Salida:
    data/gold/model/clustering_geo_dataset.parquet

Target:
    - cluster_delictivo: Cluster asignado (0-3) basado en KMeans

Uso:
    Segmentación de municipios para análisis exploratorio o para
    entrenar modelos específicos por tipo de municipio.

Anteriormente: classification_geo_clusters.parquet
"""

from pathlib import Path
import pandas as pd
from sklearn.cluster import KMeans

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

INPUT_FILE = GOLD_DIR / "gold_integrado.parquet"
OUTPUT_FILE = GOLD_DIR / "model" / "clustering_geo_dataset.parquet"

# Columnas para clustering
CLUSTER_FEATURES = ["total_delitos", "poblacion_total", "densidad_poblacional"]
N_CLUSTERS = 4


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def build_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica KMeans clustering basado en perfil delictivo.
    
    Args:
        df: DataFrame de gold_integrado
        
    Returns:
        DataFrame con columna cluster_delictivo agregada
    """
    df_out = df.copy()
    
    # Preparar features para clustering
    features = df_out[CLUSTER_FEATURES].fillna(0)
    
    # Aplicar KMeans
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df_out["cluster_delictivo"] = kmeans.fit_predict(features)
    
    return df_out


def make_clustering_geo_dataset() -> None:
    """
    Genera dataset con clusters geográficos.
    """
    print("=" * 60)
    print("CLUSTERING GEO DATASET")
    print("=" * 60)
    
    print("\nCargando gold_integrado.parquet...")
    df = pd.read_parquet(INPUT_FILE)
    print(f"  - Registros: {len(df):,}")
    
    print(f"\nAplicando KMeans con {N_CLUSTERS} clusters...")
    print(f"  Features: {CLUSTER_FEATURES}")
    df_out = build_clusters(df)
    
    # Estadísticas de clusters
    print("\n  Distribución de clusters:")
    for cluster in range(N_CLUSTERS):
        count = (df_out["cluster_delictivo"] == cluster).sum()
        pct = count / len(df_out) * 100
        
        # Estadísticas del cluster
        cluster_data = df_out[df_out["cluster_delictivo"] == cluster]
        mean_delitos = cluster_data["total_delitos"].mean()
        mean_pob = cluster_data["poblacion_total"].mean()
        
        print(f"    - Cluster {cluster}: {count:,} ({pct:.1f}%) | "
              f"Delitos promedio: {mean_delitos:.1f} | Población promedio: {mean_pob:,.0f}")
    
    # Guardar dataset
    ensure_folder(OUTPUT_FILE.parent)
    df_out.to_parquet(OUTPUT_FILE, index=False)
    
    print(f"\n✔ Dataset generado: {OUTPUT_FILE}")
    print(f"  - Filas: {len(df_out):,}")
    print(f"  - Columnas: {len(df_out.columns)}")
    print(f"  - Target: cluster_delictivo (0-{N_CLUSTERS-1})")


if __name__ == "__main__":
    make_clustering_geo_dataset()
