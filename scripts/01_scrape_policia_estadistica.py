"""
01_scrape_policia_estadistica.py
=================================

Realiza scraping de estadísticas delictivas desde la Policía Nacional.

Entrada:
    No requiere archivos de entrada. Consume HTML del sitio de la Policía.

Salida:
    data/bronze/policia_scraping/*.xlsx
"""

import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "bronze"
OUTPUT_DIR = DATA_DIR / "policia_scraping"

BASE_URL = "https://www.policia.gov.co/estadistica-delictiva"


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def slugify(text: str) -> str:
    """
    Convierte el nombre de un delito en una cadena segura para nombres de archivo:
    - Remueve acentos
    - Conserva solo letras y números
    - Reemplaza grupos de caracteres no alfanuméricos con guion bajo (_)
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    return text.strip("_")


def create_session() -> requests.Session:
    """Crea una sesión HTTP configurada con un User-Agent estándar."""
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
    return session


def get_page_html(session: requests.Session, page_number: int) -> str:
    """
    Obtiene el HTML para la página dada usando el parámetro ?page=.
    Si page_number = 0, usa la página principal sin parámetros.
    """
    params: dict[str, int] = {}
    if page_number > 0:
        params["page"] = page_number

    response = session.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.text


def parse_table_rows(html: str) -> list[tuple[str, str, str]]:
    """
    Retorna una lista de tuplas (delito, año, download_url) para una página.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Contenedor principal donde vive la tabla
    container = soup.find("div", class_="table-responsive")
    if container is not None:
        table = container.find("table")
    else:
        # Como alternativa, usar la primera tabla de la página si cambia la clase.
        table = soup.find("table")

    if table is None:
        return []

    tbody = table.find("tbody") or table
    rows: list[tuple[str, str, str]] = []

    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        crime = tds[0].get_text(strip=True)
        year = tds[1].get_text(strip=True)

        # Preferible <a class="file-link">, pero usa cualquier <a> como alternativa.
        link_tag = tds[2].find("a", class_="file-link") or tds[2].find("a")
        if link_tag is None or not link_tag.get("href"):
            continue

        href = link_tag["href"]
        download_url = urljoin(BASE_URL, href)

        rows.append((crime, year, download_url))

    return rows


def has_next_page(html: str) -> bool:
    """
    Determina si la página tiene un enlace de paginación 'Siguiente'
    (un <a> con rel="next").
    """
    soup = BeautifulSoup(html, "html.parser")
    return soup.find("a", rel="next") is not None


def download_file(
    session: requests.Session,
    crime: str,
    year: str,
    url: str,
    index: int | None = None,
) -> Path:
    """
    Descarga el archivo de Excel y lo guarda con la convención de nombres solicitada:
    {AÑO}_{DELITO}_{ÚltimaParteDelEnlace}

    Muestra el índice del archivo (index) si se proporciona.
    """
    ensure_folder(OUTPUT_DIR)
    prefix = f"[{index:03d}] " if index is not None else ""

    crime_slug = slugify(crime)

    # Elimina la cadena de consulta (querystring) en caso de que la URL contenga ?…
    last_part = Path(url.split("?", 1)[0]).name

    filename = f"{year}_{crime_slug}_{last_part}"
    dest_path = OUTPUT_DIR / filename

    if dest_path.exists():
        print(f"{prefix}[SKIP] Ya existe: {dest_path}")
        return dest_path

    print(f"{prefix}[DL  ] {year} | {crime} -> {url}")
    response = session.get(url, timeout=60)
    response.raise_for_status()

    dest_path.write_bytes(response.content)
    print(f"{prefix}[OK  ] Guardado: {dest_path}")
    return dest_path


def run_scraping() -> None:
    """Ejecuta el proceso completo de scraping y descarga de archivos."""
    session = create_session()

    total_files = 0
    page = 0

    while True:
        print(f"\n=== Procesando página {page} ===")
        html = get_page_html(session, page)
        rows = parse_table_rows(html)

        if not rows:
            print("No se encontraron filas en esta página. Deteniendo scraping.")
            break

        print(f"Se encontraron {len(rows)} archivos en la página {page}.")

        for crime, year, url in rows:
            try:
                total_files += 1
                download_file(session, crime, year, url, index=total_files)
            except Exception as exc:  # noqa: BLE001
                print(
                    f"[ERR] Error en archivo {total_files} "
                    f"({crime} {year} {url}): {exc}",
                )

        # Si no hay botón "Siguiente", terminamos
        if not has_next_page(html):
            print("No se encontró enlace 'Siguiente'. Fin de la paginación.")
            break

        # Se avanza a la siguiente página
        page += 1

        # Tiempo de espera para no saturar el servidor
        time.sleep(1)

    print(f"\nCompletado. Total de archivos procesados: {total_files}")


def main() -> None:
    """Función principal del script."""
    print("=" * 60)
    print("01 - SCRAPING POLICÍA NACIONAL (BRONZE / POLICIA_SCRAPING)")
    print("=" * 60)

    run_scraping()

    print("=" * 60)
    print("✔ Scraping completado")
    print("=" * 60)


if __name__ == "__main__":
    main()