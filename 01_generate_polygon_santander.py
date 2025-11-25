from pathlib import Path

import requests
import geopandas as gpd


def gen_pol():
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

    output_dir = Path("data/bronze/dane_geo")
    output_dir.mkdir(parents=True, exist_ok=True)

    geojson_path = output_dir / "santander_municipios.geojson"

    print(f"Guardando GeoJSON en: {geojson_path}")
    gdf_santander.to_file(geojson_path, driver="GeoJSON")

    print("Proceso completado con éxito.")

if __name__ == "__main__":
    gen_pol()
