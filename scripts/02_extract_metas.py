"""
02_extract_metas.py
====================

Convierte las tablas de metas del Plan de Desarrollo desde Excel (capa Bronze)
a formato Parquet en la capa Silver, sin transformar la estructura.

Entrada:
    data/bronze/metas/mandatos.xlsx
    data/bronze/metas/metas.xlsx

Salida:
    data/silver/metas/mandatos.parquet
    data/silver/metas/metas.parquet
"""

from pathlib import Path

import pandas as pd

# === CONFIGURACIÓN DE RUTAS ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

BRONZE_DIR = BASE_DIR / "data" / "bronze" / "metas"
SILVER_DIR = BASE_DIR / "data" / "silver" / "metas"

INPUT_MANDATOS = BRONZE_DIR / "mandatos.xlsx"
INPUT_METAS = BRONZE_DIR / "metas.xlsx"

OUTPUT_MANDATOS = SILVER_DIR / "mandatos.parquet"
OUTPUT_METAS = SILVER_DIR / "metas.parquet"


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


def load_excel(path: Path, label: str) -> pd.DataFrame:
    """Carga un archivo Excel desde la capa Bronze."""
    check_exists(path, label=label)
    print(f"➤ Cargando archivo Excel: {label}...")
    df = pd.read_excel(path)
    print(f"✔ Datos cargados ({label}): {df.shape[0]} filas, {df.shape[1]} columnas")
    return df


def save_parquet(df: pd.DataFrame, output_path: Path, label: str) -> None:
    """Guarda un DataFrame en formato Parquet en la capa Silver."""
    ensure_folder(output_path.parent)
    print(f"➤ Guardando {label} en formato Parquet...")
    df.to_parquet(output_path, index=False)
    print(f"✔ Archivo Parquet generado: {output_path}")


def main() -> None:
    """Función principal del script."""
    print("=" * 60)
    print("02 - EXTRACCIÓN METAS PLAN DE DESARROLLO (BRONZE → SILVER)")
    print("=" * 60)

    # Cargar Excel desde Bronze
    df_mandatos = load_excel(INPUT_MANDATOS, label="mandatos")
    df_metas = load_excel(INPUT_METAS, label="metas")

    # Guardar en Silver como Parquet (sin transformación)
    save_parquet(df_mandatos, OUTPUT_MANDATOS, label="mandatos")
    save_parquet(df_metas, OUTPUT_METAS, label="metas")

    print("=" * 60)
    print("✔ Proceso de extracción de metas completado")
    print("=" * 60)


if __name__ == "__main__":
    main()
