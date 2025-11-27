"""
01_scrape_policia_estadistica.py
=================================

Realiza scraping de estadísticas delictivas desde la Policía Nacional.

Fuente:
    https://www.policia.gov.co/estadistica-delictiva

Salida:
    data/bronze/policia_scraping/*.xlsx (~241 archivos)
"""

import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

BASE_URL = "https://www.policia.gov.co/estadistica-delictiva"
OUTPUT_DIR = BASE_DIR / "data" / "bronze" / "policia_scraping"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Adjusta si cambia el número de páginas del sitio
FIRST_PAGE = 0
LAST_PAGE = 30  # Inclusivo, basado en inspección previa


def slugify(text: str) -> str:
    """
    Convierte el nombre de un delito en una cadena segura para nombres de archivo:
    - Remueve acentos
    - Conserva solo letras y números
    - Reemplaza grupos de caracteres no alfanuméricos con guion bajo (_)
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    return text.strip("_")


def get_page_html(session: requests.Session, page_number: int) -> str:
    """
    Obtiene el HTML para la página dada usando el parámetro ?page=.
    """
    params = {}
    if page_number > 0:
        params["page"] = page_number

    resp = session.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_table_rows(html: str):
    """
    Retorna una lista de tuplas (delito, año, download_url) para una página.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Container principal donde vive la tabla
    container = soup.find("div", class_="table-responsive")
    if container:
        table = container.find("table")
    else:
        # Como alternativa, usar la primera tabla de la página si cambia la clase.
        table = soup.find("table")

    if not table:
        return []

    tbody = table.find("tbody") or table
    rows = []

    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        crime = tds[0].get_text(strip=True)
        year = tds[1].get_text(strip=True)

        # Preferible <a class="file-link">, pero usa cualquier <a> como alternativa.
        link_tag = tds[2].find("a", class_="file-link") or tds[2].find("a")
        if not link_tag or not link_tag.get("href"):
            continue

        href = link_tag["href"]
        download_url = urljoin(BASE_URL, href)

        rows.append((crime, year, download_url))

    return rows


def download_file(session: requests.Session, crime: str, year: str, url: str) -> Path:
    """
    Descarga el archivo de Excel y lo guarda con la convención de nombres solicitada: {AÑO}_{DELITO}_{ÚltimaParteDelEnlace}
    """
    crime_slug = slugify(crime)

    # Elimina la cadena de consulta (querystring) en caso de que la URL contenga ?….
    last_part = Path(url.split("?", 1)[0]).name

    filename = f"{year}_{crime_slug}_{last_part}"
    dest_path = OUTPUT_DIR / filename

    if dest_path.exists():
        print(f"[SKIP] Ya existe: {dest_path}")
        return dest_path

    print(f"[DL] {year} | {crime} -> {url}")
    resp = session.get(url, timeout=60)
    resp.raise_for_status()

    dest_path.write_bytes(resp.content)
    print(f"[OK ] Guardado: {dest_path}")
    return dest_path


def main() -> None:
    """Función principal del script."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        }
    )

    total_files = 0

    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        print(f"\n=== Procesando página {page} ===")
        html = get_page_html(session, page)
        rows = parse_table_rows(html)

        if not rows:
            print("No existen filas en esta página – detención temprana.")
            break

        for crime, year, url in rows:
            try:
                download_file(session, crime, year, url)
                total_files += 1
            except Exception as e:
                print(f"[ERR] Error por {crime} {year} {url}: {e}")

        # Be polite with the server
        time.sleep(1)

    print(f"\nCompletado. Total de archivos descargados: {total_files}")


if __name__ == "__main__":
    main()
