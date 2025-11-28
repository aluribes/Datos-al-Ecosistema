"""
02_process_danegeo.py
=====================

Procesa datos geográficos del DANE para la capa Silver.

Entrada:
    data/bronze/dane_geo/divipola_2010.xls
    data/bronze/dane_geo/santander_municipios.geojson

Salida:
    data/silver/dane_geo/divipola_silver.parquet
    data/silver/dane_geo/geografia_silver.parquet
    data/silver/dane_geo/geografia_silver.geojson
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import unidecode

# === CONFIGURACIÓN DE RUTAS ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Rutas de entrada
BRONZE_DIR = BASE_DIR / "data" / "bronze"
DIVIPOLA_INPUT = BRONZE_DIR / "dane_geo" / "divipola_2010.xls"
GEOJSON_INPUT = BRONZE_DIR / "dane_geo" / "santander_municipios.geojson"

# Rutas de salida
SILVER_DIR = BASE_DIR / "data" / "silver" / "dane_geo"
DIVIPOLA_OUTPUT = SILVER_DIR / "divipola_silver.parquet"
GEOGRAPHY_OUTPUT_PARQUET = SILVER_DIR / "geografia_silver.parquet"
GEOGRAPHY_OUTPUT_GEOJSON = SILVER_DIR / "geografia_silver.geojson"


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def check_exists(path: Path, label: str | None = None) -> None:
    """Verifica que un archivo exista antes de procesarlo."""
    if not path.exists():
        msg = f"❌ ERROR: No se encontró el archivo requerido:\n{path}"
        if label is not None:
            msg += f"\n(dataset: {label})"
        print(msg)
        raise FileNotFoundError(msg)

    print(f"✔ Archivo encontrado: {path}")


# =========================================================
# Funciones de carga
# =========================================================

def load_divipola(filepath: Path) -> pd.DataFrame:
    """
    Lee el archivo Divipola desde la hoja LISTADO_VIGENTES
    usando la fila de índice 2 como encabezado.
    """
    check_exists(filepath, label="DIVIPOLA 2010")
    print("➤ Cargando archivo DIVIPOLA 2010...")
    df = pd.read_excel(
        filepath,
        sheet_name="LISTADO_VIGENTES",
        header=2,
    )
    df = df.reset_index(drop=True)
    print(f"✔ DIVIPOLA cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    return df


def load_santander_geojson(filepath: Path) -> gpd.GeoDataFrame:
    """
    Lee el archivo GeoJSON de municipios de Santander con sus coordenadas.
    """
    check_exists(filepath, label="GeoJSON Santander")
    print("➤ Cargando GeoJSON de municipios de Santander...")
    gdf = gpd.read_file(filepath, encoding="utf-8")
    print(f"✔ GeoJSON cargado: {gdf.shape[0]} filas, {gdf.shape[1]} columnas")
    return gdf


# =========================================================
# Funciones de transformación
# =========================================================

def transform_divipola_to_silver(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra solo Santander, normaliza nombres y renombra columnas
    para la tabla Divipola en Silver.
    """
    print("➤ Transformando DIVIPOLA para Santander...")

    # Filtrar solo Santander
    df_santander = df[df["Nombre Departamento"].str.upper() == "SANTANDER"].copy()

    # Normalización de nombres (departamento / municipio)
    df_santander.loc[:, "Nombre Departamento"] = (
        df_santander["Nombre Departamento"]
        .str.upper()
        .map(unidecode.unidecode)
    )
    df_santander.loc[:, "Nombre Municipio"] = (
        df_santander["Nombre Municipio"]
        .str.upper()
        .map(unidecode.unidecode)
    )

    # Renombrar columnas
    rename_map = {
        "Código Departamento": "codigo_departamento",
        "Código Municipio": "codigo_municipio",
        "Código Centro Poblado": "codigo_centro_poblado",
        "Nombre Departamento": "departamento",
        "Nombre Municipio": "municipio",
        "Nombre Centro Poblado": "centro_poblado",
        "Clase": "clase",
    }

    df_santander = df_santander.rename(columns=rename_map)
    print(f"✔ DIVIPOLA transformado: {df_santander.shape[0]} filas")
    return df_santander


def transform_geojson_to_silver(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Limpia el GeoDataFrame eliminando columnas no relevantes
    y renombrando columnas clave para Silver.
    """
    print("➤ Transformando GeoJSON a formato Silver...")

    # Eliminar columnas no relevantes (si existen)
    cols_to_drop = {"MPIO_CCDGO", "MPIO_CRSLC", "MPIO_NANO"}
    cols_to_drop = [col for col in cols_to_drop if col in gdf.columns]
    gdf_clean = gdf.drop(columns=cols_to_drop, errors="ignore").copy()

    # Renombrar columnas
    rename_map = {
        "DPTO_CCDGO": "codigo_departamento",
        "MPIO_CCNCT": "codigo_municipio",
        "DPTO_CNMBR": "departamento",
        "MPIO_CNMBR": "municipio",
        "MPIO_NAREA": "area",
    }

    gdf_clean = gdf_clean.rename(columns=rename_map)

    print(f"✔ GeoDataFrame transformado: {gdf_clean.shape[0]} filas")
    return gdf_clean


# =========================================================
# Funciones de guardado
# =========================================================

def save_divipola_silver(df: pd.DataFrame, parquet_path: Path) -> None:
    """
    Guarda la tabla Divipola en formato Parquet (Silver).
    """
    ensure_folder(parquet_path.parent)
    print(f"➤ Guardando DIVIPOLA Silver en: {parquet_path}")
    df.to_parquet(parquet_path, index=False)
    print("✔ DIVIPOLA Silver guardado correctamente")


def save_geography_silver(
    gdf: gpd.GeoDataFrame,
    parquet_path: Path,
    geojson_path: Path,
) -> None:
    """
    Guarda la tabla geográfica en Parquet y GeoJSON (Silver).
    """
    ensure_folder(parquet_path.parent)

    print(f"➤ Guardando Geografía Silver (Parquet) en: {parquet_path}")
    gdf.to_parquet(parquet_path, index=False)
    print("✔ Geografía Silver (Parquet) guardada correctamente")

    print(f"➤ Guardando Geografía Silver (GeoJSON) en: {geojson_path}")
    gdf.to_file(geojson_path, driver="GeoJSON")
    print("✔ Geografía Silver (GeoJSON) guardada correctamente")


# =========================================================
# Función principal
# =========================================================

def main() -> None:
    """Función principal del script."""
    print("=" * 60)
    print("02 - PROCESAMIENTO DANE GEO (BRONZE → SILVER)")
    print("=" * 60)

    # 1. Carga de datos
    divipola_df = load_divipola(DIVIPOLA_INPUT)
    geojson_santander_gdf = load_santander_geojson(GEOJSON_INPUT)

    # 2. Transformaciones
    divipola_santander_df = transform_divipola_to_silver(divipola_df)
    geojson_santander_silver_gdf = transform_geojson_to_silver(geojson_santander_gdf)

    # 3. Guardado en Silver
    save_divipola_silver(divipola_santander_df, DIVIPOLA_OUTPUT)
    save_geography_silver(
        geojson_santander_silver_gdf,
        GEOGRAPHY_OUTPUT_PARQUET,
        GEOGRAPHY_OUTPUT_GEOJSON,
    )

    print("=" * 60)
    print("✔ Procesamiento DANE GEO completado")
    print("=" * 60)


if __name__ == "__main__":
    main()