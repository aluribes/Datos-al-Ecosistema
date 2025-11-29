#!/usr/bin/env python
"""
run_pipeline.py

Orquestador del pipeline de Datos-al-Ecosistema.

Funcionalidades:
- Detecta si es la primera ejecución (no existe o está vacía la carpeta `data/`).
- Si NO es la primera ejecución, crea un backup de `data/` en `history/AAAAMMDD_HHMMSS/`.
- Descubre los scripts en la carpeta `scripts/` y los ejecuta en orden alfabético.
- Pensado para ejecutarse bajo demanda o programado (cron, Task Scheduler).

Fases del pipeline (por prefijo):
    00_  Setup inicial (crear carpetas, configuración)
    01_  Bronze - Ingesta de datos crudos (scraping, APIs, descargas)
    02_  Silver - Limpieza y estandarización de datos
    03_  Gold - Integración y enriquecimiento de datos
    04_  Model - Generación de datasets para ML y dashboard

Scripts ejecutados (en orden alfabético):
    00_setup.py                              # Configuración inicial
    01_extract_bronze.py                     # Extracción de datos bronze
    01_generate_polygon_santander.py         # Polígonos geográficos
    01_scrape_policia_estadistica.py         # Scraping Policía Nacional
    02_datos_poblacion_santander.py          # Población DANE
    02_extract_metas.py                      # Metas del Plan de Desarrollo
    02_process_danegeo.py                    # Geografía DANE (Divipola)
    02_process_policia_completo.py           # Policía consolidado
    02_process_policia.py                    # Policía básico
    02_process_socrata.py                    # Datos abiertos Socrata
    02_socrata_bucaramanga_to_parquet.py     # Socrata Bucaramanga
    03_generate_gold.py                      # Capa Gold base
    03_process_silver_data.py                # Preparación Silver→Gold
    04_generate_analytics.py                 # Métricas analíticas
    04_generate_classification_*.py          # Datasets clasificación (3)
    04_generate_clustering_geo_dataset.py    # Dataset clustering
    04_generate_dashboard_data.py            # Datos para Streamlit
    04_generate_regression_*.py              # Datasets regresión (3)

Uso básico:
    python run_pipeline.py

Opciones:
    python run_pipeline.py --dry-run        # Muestra qué haría, sin ejecutar scripts ni copiar datos
    python run_pipeline.py --no-backup      # Ejecuta el pipeline sin crear backup de data/
    python run_pipeline.py --scripts-dir scripts_alt  # Usar otra carpeta de scripts
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

# --- Configuración básica de rutas ---

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORY_DIR = PROJECT_ROOT / "history"


# --- Utilidades generales ---

def is_first_run() -> bool:
    """
    Devuelve True si se considera que es la primera ejecución del pipeline.
    Criterio: no existe la carpeta `data/` o está vacía.
    """
    if not DATA_DIR.exists():
        return True
    # Si existe pero no tiene nada dentro, lo tratamos como primera corrida
    try:
        next(DATA_DIR.iterdir())
    except StopIteration:
        return True
    return False


def create_history_snapshot(dry_run: bool = False) -> Path | None:
    """
    Crea una copia de la carpeta `data/` dentro de `history/AAAAMMDD_HHMMSS/`.

    - Si `data/` no existe o está vacía, no hace nada y devuelve None.
    - Si `dry_run` es True, solo loguea la acción sin ejecutarla.
    """
    if not DATA_DIR.exists():
        logging.info("No existe la carpeta 'data/'. No se crea backup.")
        return None

    # Comprobamos si hay contenido en data/
    try:
        next(DATA_DIR.iterdir())
    except StopIteration:
        logging.info("La carpeta 'data/' está vacía. No se crea backup.")
        return None

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = HISTORY_DIR / timestamp

    logging.info("Creando backup de 'data/' en '%s' ...", backup_dir)

    if dry_run:
        logging.info("[DRY-RUN] Se copiaría '%s' → '%s'", DATA_DIR, backup_dir)
        return backup_dir

    backup_dir.mkdir(parents=True, exist_ok=False)

    # Copiamos el contenido de data/ dentro de history/timestamp/
    # Esto replica la ESTRUCTURA de data/ directamente dentro de la carpeta con fecha.
    shutil.copytree(DATA_DIR, backup_dir, dirs_exist_ok=True)

    logging.info("Backup creado correctamente en '%s'.", backup_dir)
    return backup_dir


def discover_scripts(scripts_dir: Path) -> List[Path]:
    """
    Descubre los scripts de pipeline en la carpeta indicada.

    Criterios:
    - Archivos *.py
    - Ignora __init__.py y archivos que empiecen por '_' (por si tienes utils).
    - Devuelve la lista ordenada alfabéticamente, para que puedas controlar
      el orden con prefijos tipo 01_, 02_, etc.
    """
    if not scripts_dir.exists():
        logging.warning("La carpeta de scripts '%s' no existe.", scripts_dir)
        return []

    scripts = sorted(
        p
        for p in scripts_dir.glob("*.py")
        if p.name != "__init__.py" and not p.name.startswith("_")
    )

    if not scripts:
        logging.warning("No se encontraron scripts .py en '%s'.", scripts_dir)
    else:
        logging.info("Scripts de pipeline encontrados (en orden de ejecución):")
        for s in scripts:
            logging.info("  - %s", s.relative_to(PROJECT_ROOT))

    return scripts


def run_script(script_path: Path, dry_run: bool = False) -> None:
    """
    Ejecuta un script Python como subproceso: `python script_path`.

    Si `dry_run` es True, no ejecuta nada, solo informa.
    Lanza excepciones si hay errores en la ejecución.
    """
    rel = script_path.relative_to(PROJECT_ROOT)

    if dry_run:
        logging.info("[DRY-RUN] Se ejecutaría: %s %s", sys.executable, rel)
        return

    logging.info("Ejecutando script: %s", rel)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logging.error("Error al ejecutar %s (returncode=%s)", rel, result.returncode)
        if result.stdout:
            logging.error("STDOUT:\n%s", result.stdout)
        if result.stderr:
            logging.error("STDERR:\n%s", result.stderr)
        # Detenemos el pipeline en el primer error
        raise RuntimeError(f"Fallo en el script {rel} (returncode={result.returncode})")

    if result.stdout:
        logging.debug("STDOUT (%s):\n%s", rel, result.stdout)
    if result.stderr:
        logging.debug("STDERR (%s):\n%s", rel, result.stderr)

    logging.info("Script finalizado correctamente: %s", rel)


def run_pipeline(scripts_dir: Path, *, do_backup: bool, dry_run: bool) -> None:
    """
    Orquesta el pipeline completo:

    1. Detecta primera ejecución.
    2. Si no es primera ejecución y do_backup=True, crea backup de data/.
    3. Descubre scripts en scripts_dir.
    4. Ejecuta scripts uno por uno en orden alfabético.
    """
    first = is_first_run()

    if first:
        logging.info("Detección: parece ser la PRIMERA ejecución del pipeline.")
        logging.info("No se realizará backup de 'data/' (no existe o está vacía).")
    else:
        logging.info("Detección: NO es la primera ejecución del pipeline.")
        if do_backup:
            create_history_snapshot(dry_run=dry_run)
        else:
            logging.info("Opción --no-backup activada: no se creará backup de 'data/'.")

    scripts = discover_scripts(scripts_dir)
    if not scripts:
        logging.error("No hay scripts para ejecutar. Pipeline abortado.")
        return

    for script in scripts:
        run_script(script, dry_run=dry_run)

    logging.info("Pipeline ejecutado completamente sin errores.")


# --- CLI / main() ---

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orquestador del pipeline de Datos-al-Ecosistema."
    )

    parser.add_argument(
        "--scripts-dir",
        type=str,
        default="scripts",
        help="Carpeta que contiene los scripts del pipeline (por defecto: 'scripts').",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="No crear backup de la carpeta 'data/' antes de correr el pipeline.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo simulación: no ejecuta scripts ni copia datos, solo muestra lo que haría.",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Muestra logs de depuración (nivel DEBUG).",
    )

    return parser.parse_args(argv)


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    scripts_dir = PROJECT_ROOT / args.scripts_dir

    logging.info("Iniciando ejecución del pipeline...")
    logging.info("Directorio del proyecto: %s", PROJECT_ROOT)
    logging.info("Directorio de datos:    %s", DATA_DIR)
    logging.info("Directorio de history:  %s", HISTORY_DIR)
    logging.info("Directorio de scripts:  %s", scripts_dir)

    try:
        run_pipeline(
            scripts_dir=scripts_dir,
            do_backup=not args.no_backup,
            dry_run=args.dry_run,
        )
    except Exception as e:
        logging.exception("El pipeline terminó con errores: %s", e)
        return 1

    logging.info("Ejecución del pipeline finalizada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
