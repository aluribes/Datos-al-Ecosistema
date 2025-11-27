"""
01_generate_polygon_santander.py
=================================

Descarga y genera el GeoJSON de municipios de Santander desde un repositorio público.

Entrada:
    No requiere archivos de entrada. Consume un GeoJSON remoto.

Salida:
    data/bronze/dane_geo/santander_municipios.geojson
"""

from pathlib import Path

import geopandas as gpd
import requests

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "bronze" / "dane_geo"

GITHUB_GEOJSON_URL = (
    "https://raw.githubusercontent.com/caticoa3/colombia_mapa/master/"
    "co_2018_MGN_MPIO_POLITICO.geojson"
)


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def download_geojson(url: str) -> dict:
    """Descarga un GeoJSON remoto y lo retorna como diccionario."""
    print("➤ Descargando GeoJSON desde GitHub...")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    print("✔ GeoJSON descargado correctamente")
    return response.json()


def filter_santander_municipalities(geojson_data: dict) -> gpd.GeoDataFrame:
    """Filtra los municipios del departamento de Santander (código 68)."""
    print("➤ Convirtiendo a GeoDataFrame...")
    gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])

    print("➤ Filtrando municipios del departamento de Santander (DPTO_CCDGO = '68')...")
    gdf_santander = gdf[gdf["DPTO_CCDGO"] == "68"].copy()

    print(f"✔ Total municipios encontrados: {gdf_santander.shape[0]}")
    return gdf_santander


def save_geojson(gdf_santander: gpd.GeoDataFrame, output_path: Path) -> None:
    """Guarda el GeoDataFrame de Santander en formato GeoJSON."""
    ensure_folder(output_path.parent)
    print(f"➤ Guardando GeoJSON en: {output_path}")
    gdf_santander.to_file(output_path, driver="GeoJSON")
    print("✔ GeoJSON guardado correctamente")


def generate_santander_polygon() -> None:
    """Orquesta la descarga, filtrado y guardado de los municipios de Santander."""
    geojson_data = download_geojson(GITHUB_GEOJSON_URL)
    gdf_santander = filter_santander_municipalities(geojson_data)
    output_path = DATA_DIR / "santander_municipios.geojson"
    save_geojson(gdf_santander, output_path)


def main() -> None:
    """Función principal del script."""
    print("=" * 60)
    print("01 - GENERACIÓN POLÍGONO SANTANDER (BRONZE / DANE_GEO)")
    print("=" * 60)

    try:
        generate_santander_polygon()
        print("=" * 60)
        print("✔ Proceso completado con éxito")
        print("=" * 60)
    except Exception as exc:  # noqa: BLE001
        print("❌ Error durante la generación del polígono de Santander:")
        print(f"   {exc}")


if __name__ == "__main__":
    main()