"""
Genera el dataset analítico enriquecido para tablero (mensual).
Entrada:  data/gold/gold_integrado.parquet
Salida:   data/gold/analytics/gold_analytics.parquet

Incluye:
1. Tasas de delito por cada 100.000 habitantes
   - Se calculan para todos los tipos de delito incluidos en el GOLD.

2. Variables estacionales basadas en estructura mensual:
   - Codificación cíclica del mes (mes_sin, mes_cos) para capturar estacionalidad.

3. Indicadores temporales derivados de TOTAL_DELITOS:
   Útiles para detectar tendencias y patrones:
   - Lags (rezagos): 1 mes, 3 meses, 12 meses.
   - Rolling means (promedios móviles): 3 y 12 meses.
   - Rolling std (desviación móvil): 3 y 12 meses.
   - pct_change: cambio porcentual mensual, trimestral y anual.

4. Indicadores de calendario por municipio y mes: (totales_mes -> para patrones estacionales)
   - Número de días laborales.
   - Número de fines de semana.
   - Número de festivos en el mes (basado en "holidays" para Colombia).

5. Información geoespacial:
   - Se conserva la columna 'geometry' para permitir mapas temáticos.
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np


# Paths

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"

INPUT_FILE = GOLD_DIR / "gold_integrado.parquet"
OUTPUT_FILE = GOLD_DIR / "analytics" / "gold_analytics.parquet"

# Utilidades

def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def save(df: gpd.GeoDataFrame, path: Path) -> None:
    """Guarda GeoDataFrame en formato parquet."""
    ensure_folder(path.parent)
    df.to_parquet(path, index=False)

# Carga de datos

def load_gold_integrado() -> gpd.GeoDataFrame:
    print(f"✔ Cargando GOLD integrado desde {INPUT_FILE}")
    return gpd.read_parquet(INPUT_FILE)

# Detección automática de columnas de delito

def detect_delito_columns(df: pd.DataFrame):
    """Detecta columnas numéricas de delitos excepto total_delitos."""
    numeric_cols = df.select_dtypes(include=["int", "float"]).columns
    delitos = [c for c in numeric_cols if c.isupper() and c not in ["TOTAL_DELITOS"]]
    return delitos


def build_analytics(df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:

    df = df.copy()

    # Fechas
    df = df.sort_values(["codigo_municipio", "anio", "mes"])
    df["fecha_proper"] = pd.to_datetime(df["anio_mes"], format="%Y-%m")

    # 1 — Tasas por 100k
    delitos_cols = detect_delito_columns(df)
    print("Columnas de delitos detectadas:", delitos_cols)

    for col in delitos_cols:
        df[f"tasa_{col.lower()}"] = (df[col] / df["poblacion_total"]) * 100000

    # 2 — Codificación cíclica
    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)

    # 3 — Lags y rolling
    grp = df.groupby("codigo_municipio")["total_delitos"]

    df["lag_1"] = grp.shift(1)
    df["lag_3"] = grp.shift(3)
    df["lag_12"] = grp.shift(12)

    df["roll_mean_3"] = grp.rolling(3).mean().reset_index(level=0, drop=True)
    df["roll_mean_12"] = grp.rolling(12).mean().reset_index(level=0, drop=True)

    df["roll_std_3"] = grp.rolling(3).std().reset_index(level=0, drop=True)
    df["roll_std_12"] = grp.rolling(12).std().reset_index(level=0, drop=True)

    df["pct_change_1"] = grp.pct_change(1)
    df["pct_change_3"] = grp.pct_change(3)
    df["pct_change_12"] = grp.pct_change(12)

    return df


def make_analytics():
    print("📌 Cargando GOLD Integrado…")
    df = gpd.read_parquet(INPUT_FILE)

    df_analytics = build_analytics(df)

    save(df_analytics, OUTPUT_FILE)
    print(f"✔ Archivo generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    make_analytics()
