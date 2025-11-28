"""
02_socrata_bucaramanga_to_parquet.py
====================================

Convierte archivos JSON de Socrata a Parquet sin transformar su contenido,
para la capa Silver.

Entrada:
    data/bronze/socrata_api/bucaramanga_delictiva_150.json
    data/bronze/socrata_api/bucaramanga_delitos_40.json
    data/bronze/socrata_api/delitos_informaticos.json

Salida:
    data/silver/socrata_api/bucaramanga_delictiva_150.parquet
    data/silver/socrata_api/bucaramanga_delitos_40.parquet
    data/silver/socrata_api/delitos_informaticos.parquet
"""

from pathlib import Path
from typing import List

import pandas as pd

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

BRONZE_DIR = BASE_DIR / "data" / "bronze" / "socrata_api"
SILVER_DIR = BASE_DIR / "data" / "silver" / "socrata_api"

# Archivos a procesar (sin extensión)
SOC_RAWS: List[str] = [
    "bucaramanga_delictiva_150",
    "bucaramanga_delitos_40",
    "delitos_informaticos",
]


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def check_exists(path: Path, label: str | None = None) -> None:
    """Verifica que un archivo exista antes de procesarlo."""
    if not path.exists():
        msg = f"❌ ERROR: No se encontró el archivo requerido:\n{path}"
        if label is not None:
            msg += f"\n(dataset: {label})"
        print(msg)
        raise FileNotFoundError(msg)
    print(f"✔ Archivo encontrado: {path}")


def convert_json_to_parquet(stem: str) -> None:
    """
    Lee un JSON Bronze y lo guarda en Silver como Parquet sin modificaciones.
    """
    input_path = BRONZE_DIR / f"{stem}.json"
    output_path = SILVER_DIR / f"{stem}.parquet"

    check_exists(input_path, label=stem)

    print(f"\n➤ Procesando dataset: {stem}")
    print(f"   Leyendo JSON desde: {input_path}")

    df = pd.read_json(input_path)

    print(f"   Registros leídos: {len(df):,}")
    print(f"   Columnas: {list(df.columns)}")

    df.to_parquet(output_path, engine="fastparquet", index=False)

    print(f"   ✅ Guardado Parquet en: {output_path}")


def main() -> None:
    """Función principal del script."""
    print("=" * 60)
    print("02 - CONVERSIÓN SOCRATA JSON → PARQUET (SILVER)")
    print("=" * 60)

    ensure_folder(SILVER_DIR)

    for stem in SOC_RAWS:
        try:
            convert_json_to_parquet(stem)
        except Exception as exc:  # noqa: BLE001
            print(f"   ✗ Error procesando '{stem}': {exc}")

    print("\n✔ Proceso de conversión finalizado")
    print("=" * 60)


if __name__ == "__main__":
    main()
