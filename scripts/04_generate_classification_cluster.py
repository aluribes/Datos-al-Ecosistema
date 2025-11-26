# 04_generate_classification_extra.py
"""
Genera múltiples datasets secundarios de clasificación:
1. delito_dominante
2. arma_dominante
3. delitos_categoria_simple
4. clusters_municipio (perfil delictivo)
"""

from pathlib import Path
import pandas as pd
from sklearn.cluster import KMeans

BASE = Path(__file__).resolve().parent.parent
GOLD = BASE / "data" / "gold"
MODEL = GOLD / "model"

POL = GOLD / "base" / "policia_gold.parquet"
INT = GOLD / "gold_integrado.parquet"

def ensure(x): x.mkdir(parents=True, exist_ok=True)

def delito_dominante(df):
    dom = (
        df.groupby(["codigo_municipio","anio","mes","delito"])
            .size()
            .reset_index(name="count")
    )
    return dom.loc[dom.groupby(["codigo_municipio","anio","mes"])["count"].idxmax()]

def arma_dominante(df):
    dom = (
        df.groupby(["codigo_municipio","anio","mes","armas_medios"])
            .size()
            .reset_index(name="count")
    )
    return dom.loc[dom.groupby(["codigo_municipio","anio","mes"])["count"].idxmax()]

def clusters(df_int):
    feats = df_int[["total_delitos","poblacion_total","densidad_poblacional"]].fillna(0)
    kmeans = KMeans(n_clusters=4, random_state=42).fit(feats)
    out = df_int.copy()
    out["cluster_delictivo"] = kmeans.labels_
    return out

def make():
    pol = pd.read_parquet(POL)
    inte = pd.read_parquet(INT)

    ensure(MODEL)

    delito_dominante(pol).to_parquet(MODEL/"classification_dominant_crime.parquet", index=False)
    arma_dominante(pol).to_parquet(MODEL/"classification_dominant_weapon.parquet", index=False)
    clusters(inte).to_parquet(MODEL/"classification_geo_clusters.parquet", index=False)

    print("✔ Archivos extra generados en:", MODEL)

if __name__ == "__main__":
    make()
