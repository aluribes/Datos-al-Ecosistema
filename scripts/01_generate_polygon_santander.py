"""
01_generate_polygon_santander.py
=================================

Descarga el GeoJSON de municipios de Santander desde GitHub.

Fuente:
    https://github.com/caticoa3/colombia_mapa

Salida:
    data/bronze/dane_geo/santander_municipios.geojson
"""

from pathlib import Path

import geopandas as gpd
import requests

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


def generate_santander_polygon() -> None:
    url = "https://raw.githubusercontent.com/caticoa3/colombia_mapa/master/co_2018_MGN_MPIO_POLITICO.geojson"

    # Descargar archivo
    print("Descargando GeoJSON desde GitHub...")
    response = requests.get(url)
    response.raise_for_status()

    geojson_data = response.json()

    print("Convirtiendo a GeoDataFrame...")
    gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])

    print("Filtrando municipios del departamento de Santander...")
    gdf_santander = gdf[gdf["DPTO_CCDGO"] == "68"].copy()

    print(f"Total municipios encontrados: {gdf_santander.shape[0]}")

    output_dir = BASE_DIR / "data" / "bronze" / "dane_geo"
    output_dir.mkdir(parents=True, exist_ok=True)

    geojson_path = output_dir / "santander_municipios.geojson"

    print(f"Guardando GeoJSON en: {geojson_path}")
    gdf_santander.to_file(geojson_path, driver="GeoJSON")

    print("Proceso completado con éxito.")

def main() -> None:
    """Función principal del script."""
    generate_santander_polygon()


if __name__ == "__main__":
    main()
