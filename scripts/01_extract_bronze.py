"""
01_extract_bronze.py
====================

Extrae datos crudos de múltiples fuentes para la capa Bronze.

Fuentes:
    - Socrata API (datos.gov.co)
    - DANE (Divipola)
    - Policía Nacional (Excel 2025)

Salida:
    data/bronze/socrata_api/*.json
    data/bronze/dane_geo/divipola_2010.xls
    data/bronze/policia_scraping/*.xlsx
"""

from pathlib import Path
import urllib.parse

import pandas as pd
import requests
from sodapy import Socrata

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
SOCRATA_TOKEN = None
CLIENT = Socrata("www.datos.gov.co", SOCRATA_TOKEN)
DATA_DIR = BASE_DIR / "data" / "bronze"

# ---------------------------------------------------------
# 1. EXTRACCIÓN SOCRATA (DATOS.GOV.CO)
# ---------------------------------------------------------
def extract_socrata() -> None:
    print("--- Iniciando extracción Socrata ---")
    datasets = {
        "delitos_sexuales": "fpe5-yrmw",
        "violencia_intrafamiliar": "vuyt-mqpw",
        "hurto_modalidades": "d4fr-sbn2",
        "bucaramanga_delictiva_150": "x46e-abhz",
        "bucaramanga_delitos_40": "75fz-q98y",
        "delitos_informaticos": "4v6r-wu98"
    }
    
    for name, id_code in datasets.items():
        print(f"Descargando: {name} ({id_code})...")
        try:
            results = CLIENT.get(id_code)
            
            df = pd.DataFrame.from_records(results)
            if not df.empty:
                # Guardamos en JSON para preservar estructura raw
                path = DATA_DIR / "socrata_api" / f"{name}.json"
                df.to_json(path, orient='records')
                print(f"Guardado en {path}")
            else:
                print(f"Advertencia: {name} retornó vacío con el filtro.")
        except Exception as e:
            print(f"Error en {name}: {e}")

# ---------------------------------------------------------
# 2. EXTRACCIÓN DANE (EXCEL DIRECTO)
# ---------------------------------------------------------
def extract_dane() -> None:
    print("\n--- Iniciando extracción DANE ---")
    url = "https://geoportal.dane.gov.co/descargas/metadatos/historicos/archivos/Listado_2010.xls"
    path = DATA_DIR / "dane_geo" / "divipola_2010.xls"
    
    try:
        response = requests.get(url, verify=False) # verify=False a veces necesario en gobierno
        with open(path, 'wb') as f:
            f.write(response.content)
        print(f"DANE Divipola guardado en {path}")
    except Exception as e:
        print(f"Error DANE: {e}")

# ---------------------------------------------------------
# 3. SCRAPING POLICÍA NACIONAL (2025)
# ---------------------------------------------------------
def extract_policia_scraping() -> None:
    print("\n--- Iniciando Scraping Policía Nacional ---")
    base_url = "https://www.policia.gov.co"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    # Lógica Especial 2025 (Links de Office Viewer)
    # Decodificamos el parámetro 'src'
    print("Procesando archivos 2025...")
    links_2025_viewer = [
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FDelitos%2520sexuales_8.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHurto%2520a%2520residencias_8.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FViolencia%2520intrafamiliar_7.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHurto%2520a%2520comercio_7.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FLesiones%2520personales_8.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FExtorsi%25C3%25B3n_8.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHurto%2520a%2520cabezas%2520de%2520ganado_7.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHurto%2520pirater%25C3%25ADa%2520terrestre_5.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHurto%2520a%2520entidades%2520Financieras_8.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHomicidio%2520Intencional_5.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FAmenazas_8.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FSecuestro_7.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FLesiones%2520en%2520accidente%2520de%2520tr%25C3%25A1nsito_6.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHurto%2520a%2520personas_8.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHomicidios%2520en%2520accidente%2520de%2520tr%25C3%25A1nsito_6.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FTerrorismo_7.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHurto%2520a%2520motocicletas_5.xlsx&wdOrigin=BROWSELINK",
        "https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.policia.gov.co%2Fsites%2Fdefault%2Ffiles%2Fdelitos-impacto%2FHurto%2520automotores_5.xlsx&wdOrigin=BROWSELINK"
    ]
    
    for viewer_url in links_2025_viewer:
        try:
            parsed = urllib.parse.urlparse(viewer_url)
            params = urllib.parse.parse_qs(parsed.query)
            if 'src' in params:
                real_url = params['src'][0] # URL real del Excel
                file_name = "2025_" + Path(real_url).name
                
                save_path = DATA_DIR / "policia_scraping" / file_name
                
                r = requests.get(real_url, headers=headers)
                with open(save_path, 'wb') as f:
                    f.write(r.content)
                print(f"Descargado 2025: {file_name}")
        except Exception as e:
            print(f"Error link 2025: {e}")

def main() -> None:
    """Ejecuta todas las extracciones de datos Bronze."""
    extract_socrata()
    extract_dane()
    extract_policia_scraping()


if __name__ == "__main__":
    main()