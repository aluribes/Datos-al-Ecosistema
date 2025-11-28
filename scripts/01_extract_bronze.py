"""
01_extract_bronze.py
====================

Extrae datos crudos de Socrata API para la capa Bronze.
Filtra SOLO registros del departamento de SANTANDER.

Entrada:
    No requiere archivos de entrada (consulta APIs externas).

Salida:
    data/bronze/socrata_api/*.json (solo Santander)
    data/bronze/dane_geo/divipola_2010.xls

Datasets Socrata:
    - HOMICIDIOS: m8fd-ahd9
    - EXTORSION: q2ib-t9am
    - HURTO_PERSONAS: 4rxi-8m8d
    - LESIONES: jr6v-i33g
    - AMENAZAS: meew-mguv
    - DELITOS_SEXUALES: fpe5-yrmw
    - VIOLENCIA_INTRAFAMILIAR: vuyt-mqpw
"""

from pathlib import Path

import pandas as pd
import requests
from sodapy import Socrata

# === CONFIGURACIÓN ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "bronze"

SOCRATA_DOMAIN = "www.datos.gov.co"
SOCRATA_TOKEN: str | None = None
CLIENT = Socrata(SOCRATA_DOMAIN, SOCRATA_TOKEN)

# Datasets de delitos con sus IDs de Socrata
DATASETS: dict[str, str] = {
    "homicidios": "m8fd-ahd9",
    "extorsion": "q2ib-t9am",
    "hurto_personas": "4rxi-8m8d",
    "lesiones": "jr6v-i33g",
    "amenazas": "meew-mguv",
    "delitos_sexuales": "fpe5-yrmw",
    "violencia_intrafamiliar": "vuyt-mqpw",
}

# Código departamento Santander
SANTANDER_CODE = "68"


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 1. EXTRACCIÓN SOCRATA (DATOS.GOV.CO) - SOLO SANTANDER
# ---------------------------------------------------------
def extract_socrata() -> None:
    """
    Extrae datasets de Socrata API (datos.gov.co).
    Filtra SOLO registros del departamento de SANTANDER.
    
    IMPORTANTE: Usamos get_all() para obtener TODOS los registros.
    El método get() por defecto solo retorna 1000 registros.
    """
    print("=" * 60)
    print("📦 EXTRACCIÓN BRONZE - SOCRATA API")
    print("=" * 60)
    print(f"Filtrando: Solo departamento SANTANDER (código {SANTANDER_CODE})")

    output_dir = DATA_DIR / "socrata_api"
    ensure_folder(output_dir)

    for name, dataset_id in DATASETS.items():
        print(f"\n📊 Descargando: {name} ({dataset_id})...")
        try:
            # Primero obtenemos una muestra para ver la estructura
            sample = CLIENT.get(dataset_id, limit=1)
            if not sample:
                print("  ⚠️ Dataset vacío")
                continue

            columns = list(sample[0].keys())

            # Determinar columna de departamento según estructura
            dept_filter: str | None = None

            if "departamento" in columns:
                dept_filter = "upper(departamento) = 'SANTANDER'"
            elif "departamento_hecho" in columns:
                dept_filter = "upper(departamento_hecho) = 'SANTANDER'"
            elif "cod_depto" in columns:
                dept_filter = f"cod_depto = '{SANTANDER_CODE}'"
            elif "codigo_dane" in columns:
                dept_filter = f"starts_with(codigo_dane, '{SANTANDER_CODE}')"

            if dept_filter:
                print(f"  Filtro: {dept_filter}")
                results = CLIENT.get_all(dataset_id, where=dept_filter)
            else:
                print("  ⚠️ No se encontró columna de departamento, descargando todo...")
                print(f"  Columnas disponibles: {columns}")
                results = CLIENT.get_all(dataset_id)

            results_list = list(results)
            print(f"  Registros Santander: {len(results_list):,}")

            if results_list:
                df = pd.DataFrame.from_records(results_list)
                output_path = output_dir / f"{name}.json"
                df.to_json(output_path, orient="records", force_ascii=False, indent=2)
                print(f"  ✔ Guardado en: {output_path}")
            else:
                print("  ⚠️ Sin registros para Santander")

        except Exception as exc:  # noqa: BLE001
            print(f"  ❌ Error: {exc}")


# ---------------------------------------------------------
# 2. EXTRACCIÓN DANE (EXCEL DIRECTO)
# ---------------------------------------------------------
def extract_dane() -> None:
    """Descarga el archivo DIVIPOLA 2010 desde el DANE."""
    print("\n" + "=" * 60)
    print("📦 EXTRACCIÓN DANE - DIVIPOLA")
    print("=" * 60)

    url = (
        "https://geoportal.dane.gov.co/descargas/metadatos/historicos/"
        "archivos/Listado_2010.xls"
    )
    output_dir = DATA_DIR / "dane_geo"
    ensure_folder(output_dir)

    output_path = output_dir / "divipola_2010.xls"

    try:
        response = requests.get(url, verify=False, timeout=60)  # noqa: S501
        response.raise_for_status()
        output_path.write_bytes(response.content)
        print(f"  ✔ DANE DIVIPOLA guardado en: {output_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ❌ Error en descarga DANE: {exc}")


# ---------------------------------------------------------
# 3. LIMPIAR DATOS ANTERIORES
# ---------------------------------------------------------
def clean_previous_data() -> None:
    """Elimina los archivos JSON anteriores de Socrata."""
    print("=" * 60)
    print("🧹 LIMPIANDO DATOS ANTERIORES")
    print("=" * 60)

    socrata_dir = DATA_DIR / "socrata_api"
    if socrata_dir.exists():
        for f in socrata_dir.glob("*.json"):
            print(f"  Eliminando: {f.name}")
            f.unlink()
        print("  ✔ Datos anteriores eliminados")
    else:
        print("  No hay datos anteriores")


def main() -> None:
    """Ejecuta todas las extracciones de datos Bronze."""
    print("=" * 60)
    print("01 - EXTRACCIÓN CAPA BRONZE (SOCRATA + DANE)")
    print("=" * 60)

    clean_previous_data()
    extract_socrata()
    extract_dane()

    print("\n" + "=" * 60)
    print("✔ Extracción Bronze completada")
    print("=" * 60)


if __name__ == "__main__":
    main()
