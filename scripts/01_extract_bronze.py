"""
01_extract_bronze.py
====================

Extrae datos crudos de múltiples fuentes para la capa Bronze.

Entrada:
    No requiere archivos de entrada (consulta APIs externas).

Salida:
    data/bronze/socrata_api/*.json
    data/bronze/dane_geo/divipola_2010.xls
"""

from pathlib import Path

import pandas as pd
import requests
from sodapy import Socrata

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "bronze"

SOCRATA_DOMAIN = "www.datos.gov.co"
SOCRATA_TOKEN: str | None = None
CLIENT = Socrata(SOCRATA_DOMAIN, SOCRATA_TOKEN)


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 1. EXTRACCIÓN SOCRATA (DATOS.GOV.CO)
# ---------------------------------------------------------
def extract_socrata() -> None:
    """Extrae datasets desde Socrata y los guarda en formato JSON."""
    print("➤ Iniciando extracción Socrata...")

    datasets: dict[str, str] = {
        "delitos_sexuales": "fpe5-yrmw",
        "violencia_intrafamiliar": "vuyt-mqpw",
        "hurto_modalidades": "d4fr-sbn2",
        "bucaramanga_delictiva_150": "x46e-abhz",
        "bucaramanga_delitos_40": "75fz-q98y",
        "delitos_informaticos": "4v6r-wu98",
    }

    output_dir = DATA_DIR / "socrata_api"
    ensure_folder(output_dir)

    for name, dataset_id in datasets.items():
        print(f"  ➤ Descargando: {name} ({dataset_id})...")
        try:
            results = CLIENT.get(dataset_id)
            df = pd.DataFrame.from_records(results)

            if df.empty:
                print(f"  ⚠️ Advertencia: {name} retornó vacío.")
                continue

            output_path = output_dir / f"{name}.json"
            df.to_json(output_path, orient="records")
            print(f"  ✔ Guardado en: {output_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ❌ Error en {name}: {exc}")


# ---------------------------------------------------------
# 2. EXTRACCIÓN DANE (EXCEL DIRECTO)
# ---------------------------------------------------------
def extract_dane() -> None:
    """Descarga el archivo DIVIPOLA 2010 desde el DANE."""
    print("\n➤ Iniciando extracción DANE...")

    url = (
        "https://geoportal.dane.gov.co/descargas/metadatos/historicos/"
        "archivos/Listado_2010.xls"
    )
    output_dir = DATA_DIR / "dane_geo"
    ensure_folder(output_dir)

    output_path = output_dir / "divipola_2010.xls"

    try:
        # verify=False a veces necesario en sitios de gobierno con certificados incompletos
        response = requests.get(url, verify=False, timeout=60)  # noqa: S501
        response.raise_for_status()

        output_path.write_bytes(response.content)
        print(f"  ✔ DANE DIVIPOLA guardado en: {output_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ❌ Error en descarga DANE: {exc}")


def main() -> None:
    """Ejecuta todas las extracciones de datos Bronze (Socrata + DANE)."""
    print("=" * 60)
    print("01 - EXTRACCIÓN CAPA BRONZE (SOCRATA + DANE)")
    print("=" * 60)

    extract_socrata()
    extract_dane()

    print("=" * 60)
    print("✔ Extracción Bronze completada")
    print("=" * 60)


if __name__ == "__main__":
    main()