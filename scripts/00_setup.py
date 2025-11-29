"""
00_setup.py
===========

Crea la estructura de carpetas base del proyecto.

Entrada:
    No requiere archivos de entrada.

Salida:
    data/bronze/              - Datos crudos (sin procesar)
        socrata_api/          - JSONs de la API Socrata de Bucaramanga
        policia_scraping/     - Excels descargados de Policía Nacional
        dane_geo/             - Datos geográficos DANE (DIVIPOLA, GeoJSON)
        poblacion_dane/       - Datos de población DANE (ZIPs)
        metas/                - Datos de metas departamentales
    data/silver/              - Datos limpios (procesados)
        socrata_api/          - Parquets procesados de Socrata
        policia_scraping/     - Parquets procesados de Policía
        dane_geo/             - Parquets geográficos procesados
        poblacion/            - Parquet de población Santander
        delitos/              - Consolidado de delitos
        metas/                - Parquets de metas procesadas
    data/gold/                - Datos integrados (listos para análisis)
        base/                 - Parquets gold individuales (geo, policia, socrata, poblacion, divipola)
        analytics/            - Datos analíticos agregados
        model/                - Datasets para modelos ML
        dashboard/            - Datos para dashboard
"""

from pathlib import Path

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def create_structure() -> None:
    """Crea la estructura de carpetas de las capas Bronze, Silver y Gold."""
    # Subcarpetas para Bronze
    bronze_subfolders = [
        "socrata_api",
        "policia_scraping",
        "dane_geo",
        "poblacion_dane",
        "metas",
    ]

    # Subcarpetas para Silver
    silver_subfolders = [
        "socrata_api",
        "policia_scraping",
        "dane_geo",
        "poblacion",
        "delitos",
        "metas",
    ]

    # Subcarpetas para Gold
    gold_subfolders = [
        "base",
        "analytics",
        "model",
        "dashboard",
    ]

    # Crear estructura para bronze
    for sub in bronze_subfolders:
        path = DATA_DIR / "bronze" / sub
        ensure_folder(path)
        print(f"✔ Creado: {path}")

    # Crear estructura para silver
    for sub in silver_subfolders:
        path = DATA_DIR / "silver" / sub
        ensure_folder(path)
        print(f"✔ Creado: {path}")

    # Crear estructura para gold
    for sub in gold_subfolders:
        path = DATA_DIR / "gold" / sub
        ensure_folder(path)
        print(f"✔ Creado: {path}")


def main() -> None:
    """Función principal del script."""
    print("=" * 60)
    print("00 - SETUP ESTRUCTURA DE CARPETAS")
    print("=" * 60)

    create_structure()

    print("=" * 60)
    print("✔ Estructura base creada correctamente")
    print("=" * 60)


if __name__ == "__main__":
    main()