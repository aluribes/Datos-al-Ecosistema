"""
00_setup.py
===========

Crea la estructura de carpetas base del proyecto.

Entrada:
    No requiere archivos de entrada.

Salida:
    data/bronze/              - Datos crudos
        socrata_api/
        policia_scraping/
        dane_geo/
    data/silver/              - Datos limpios
        socrata_api/
        policia_scraping/
        dane_geo/
    data/gold/                - Datos integrados
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
    # Capas que tendrán subcarpetas
    layers_with_subfolders = ["bronze", "silver"]

    # Subcarpetas para organizar mejor
    subfolders = ["socrata_api", "policia_scraping", "dane_geo"]

    # Crear estructura para bronze y silver
    for layer in layers_with_subfolders:
        for sub in subfolders:
            path = DATA_DIR / layer / sub
            ensure_folder(path)
            print(f"✔ Creado: {path}")

    # Crear solo la carpeta gold (sin subcarpetas)
    gold_path = DATA_DIR / "gold"
    ensure_folder(gold_path)
    print(f"✔ Creado: {gold_path}")


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