import pandas as pd
import geopandas as gpd
from pathlib import Path
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
GEOGRAFIA_OUTPUT_PARQUET = SILVER_DIR / "geografia_silver.parquet"
GEOGRAFIA_OUTPUT_GEOJSON = SILVER_DIR / "geografia_silver.geojson"


# Funciones de carga

def load_divipola(filepath: Path) -> pd.DataFrame:
    """
    Lee el archivo Divipola desde la hoja LISTADO_VIGENTES
    usando la fila de índice 2 como encabezado.
    """
    df = pd.read_excel(
        filepath,
        sheet_name="LISTADO_VIGENTES",
        header=2
    )
    df = df.reset_index(drop=True)
    return df


def load_santander_geojson(filepath: Path) -> gpd.GeoDataFrame:
    """
    Lee el archivo GeoJSON de municipios de Santander con sus coordenadas.
    """
    gdf = gpd.read_file(filepath, encoding="utf-8")
    return gdf


# Funciones de transformación

def transform_divipola_to_silver(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra solo Santander, normaliza nombres y renombra columnas
    para la tabla Divipola en Silver.
    """
    # Filtrar solo Santander (ignorando mayúsculas/minúsculas por seguridad)
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

    return df_santander


def transform_geojson_to_silver(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Limpia el GeoDataFrame eliminando columnas no relevantes
    y renombrando columnas clave para Silver.
    """
    # Eliminar columnas no relevantes (si existen)
    cols_to_drop = {"MPIO_CCDGO", "MPIO_CRSLC", "MPIO_NANO"}
    cols_to_drop = [c for c in cols_to_drop if c in gdf.columns]
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

    return gdf_clean


# Funciones de guardado

def save_divipola_silver(df: pd.DataFrame, parquet_path: Path) -> None:
    """
    Guarda la tabla Divipola en formato Parquet (Silver).
    """
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, engine="fastparquet", index=False)


def save_geografia_silver(
    gdf: gpd.GeoDataFrame,
    parquet_path: Path,
    geojson_path: Path
) -> None:
    """
    Guarda la tabla geográfica en Parquet y GeoJSON (Silver).
    """
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    # Parquet (geometry en formato WKB/WKT según engine)
    gdf.to_parquet(parquet_path, engine="pyarrow", index=False)

    # GeoJSON para uso en herramientas GIS / web
    gdf.to_file(geojson_path, driver="GeoJSON")


# Función principal

def main() -> None:
    # 1. Carga de datos
    divipola_df = load_divipola(DIVIPOLA_INPUT)
    geojson_santander_gdf = load_santander_geojson(GEOJSON_INPUT)

    # 2. Transformaciones
    divipola_santander_df = transform_divipola_to_silver(divipola_df)
    geojson_santander_silver_gdf = transform_geojson_to_silver(geojson_santander_gdf)

    # 3. Guardado en Silver
    save_divipola_silver(divipola_santander_df, DIVIPOLA_OUTPUT)
    save_geografia_silver(
        geojson_santander_silver_gdf,
        GEOGRAFIA_OUTPUT_PARQUET,
        GEOGRAFIA_OUTPUT_GEOJSON,
    )

    print("✅ Divipola Silver guardado en:", DIVIPOLA_OUTPUT)
    print("✅ Geografía Silver guardada en:")
    print("   -", GEOGRAFIA_OUTPUT_PARQUET)
    print("   -", GEOGRAFIA_OUTPUT_GEOJSON)


if __name__ == "__main__":
    main()