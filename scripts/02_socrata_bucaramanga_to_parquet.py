"""
02_socrata_bucaramanga_to_parquet.py
====================================

Convierte y limpia archivos JSON de Socrata a Parquet para la capa Silver.

Entrada (Bronze):
    data/bronze/socrata_api/bucaramanga_delictiva_150.json
    data/bronze/socrata_api/bucaramanga_delitos_40.json
    data/bronze/socrata_api/delitos_informaticos.json

Salida (Silver):
    data/silver/socrata_api/bucaramanga_delitos.parquet       # Bucaramanga unificado y sin duplicados
    data/silver/socrata_api/delitos_informaticos.parquet      # Delitos informáticos limpio

Transformaciones principales:
    - Columnas en minúscula y formato snake_case (nombre_columna)
    - Unificación de las dos bases de Bucaramanga y eliminación de duplicados
    - Normalización de nombres de columnas para alinearlos con otros datasets:
        * cod_mun, cod_muni, cod_mpio, codigo_mun -> codigo_municipio
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
BUCARAMANGA_STEMS: List[str] = [
    "bucaramanga_delictiva_150",
    "bucaramanga_delitos_40",
]

DELITOS_INF_STEM = "delitos_informaticos"

BUCARAMANGA_OUTPUT = "bucaramanga_delitos.parquet"
DELITOS_INF_OUTPUT = "delitos_informaticos.parquet"


# =========================================================
# Utilidades generales
# =========================================================

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


def to_snake_case(name: str) -> str:
    """
    Convierte un nombre de columna a snake_case en minúsculas.
    Ejemplos:
        "COD_MUN"        -> "cod_mun"
        "Cod Mun"        -> "cod_mun"
        "Código Municipio" -> "código_municipio"
    (sin eliminar tildes, solo formateo básico)
    """
    # Pasar a string por seguridad
    text = str(name)
    # Quitar espacios al inicio/fin
    text = text.strip()
    # Reemplazar espacios y separadores comunes por guion bajo
    for sep in [" ", "-", "/", "."]:
        text = text.replace(sep, "_")
    # Normalizar dobles guiones bajos
    while "__" in text:
        text = text.replace("__", "_")
    # A minúsculas
    return text.lower()


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza los nombres de columnas:
        - minúscula
        - snake_case
        - mapea columnas específicas a nombres estándar del modelo (p.ej. codigo_municipio)
    """
    # 1. snake_case genérico
    df = df.copy()
    new_cols = {col: to_snake_case(col) for col in df.columns}
    df = df.rename(columns=new_cols)

    # 2. Mapeo específico para alinearse con otros datasets
    #    (puedes ir ajustando este diccionario según veas más columnas)
    rename_map = {
        "cod_mun": "codigo_municipio",
        "cod_muni": "codigo_municipio",
        "cod_mpio": "codigo_municipio",
        "codigo_mun": "codigo_municipio",
        "codigo_dane_municipio": "codigo_municipio",
        # Por si viniera algo como "cod_municipio"
        "cod_municipio": "codigo_municipio",
    }

    df = df.rename(columns={old: new for old, new in rename_map.items() if old in df.columns})

    return df


# =========================================================
# Carga y limpieza de JSON
# =========================================================

def load_and_clean_json(stem: str) -> pd.DataFrame:
    """
    Lee un JSON Bronze, estandariza nombres de columnas y retorna el DataFrame.
    No aplica filtros de filas, solo limpieza de nombres.
    """
    input_path = BRONZE_DIR / f"{stem}.json"
    check_exists(input_path, label=stem)

    print(f"\n➤ Cargando dataset: {stem}")
    print(f"   Leyendo JSON desde: {input_path}")

    df = pd.read_json(input_path)

    print(f"   Registros raw: {len(df):,}")
    print(f"   Columnas raw: {list(df.columns)}")

    df = standardize_column_names(df)

    print(f"   Columnas estandarizadas: {list(df.columns)}")

    return df


# =========================================================
# Procesos específicos
# =========================================================

def process_bucaramanga() -> None:
    """
    Procesa los dos datasets de Bucaramanga:
        - bucaramanga_delictiva_150
        - bucaramanga_delitos_40

    Unifica ambos en un solo DataFrame, elimina duplicados
    y los guarda en un único Parquet en Silver.
    """
    print("\n" + "-" * 60)
    print("🏙  PROCESANDO BUCARAMANGA (UNIFICAR + LIMPIAR)")
    print("-" * 60)

    dataframes: list[pd.DataFrame] = []

    for stem in BUCARAMANGA_STEMS:
        df_stem = load_and_clean_json(stem)

        if df_stem.empty:
            print(f"   ⚠ Dataset vacío: {stem}")
        else:
            print(f"   ✔ Dataset {stem} con {len(df_stem):,} filas")
            dataframes.append(df_stem)

    if not dataframes:
        print("   ❌ No hay datos de Bucaramanga para procesar.")
        return

    # Unificar y eliminar duplicados
    df_bucaramanga = pd.concat(dataframes, ignore_index=True)

    rows_before = len(df_bucaramanga)
    df_bucaramanga = df_bucaramanga.drop_duplicates()
    rows_after = len(df_bucaramanga)

    print(f"\n   Filas unificadas antes de eliminar duplicados: {rows_before:,}")
    print(f"   Filas después de eliminar duplicados:         {rows_after:,}")

    ensure_folder(SILVER_DIR)
    output_path = SILVER_DIR / BUCARAMANGA_OUTPUT

    df_bucaramanga.to_parquet(output_path, engine="fastparquet", index=False)

    print(f"\n   ✅ Bucaramanga unificado guardado en: {output_path}")
    print(f"      Registros finales: {len(df_bucaramanga):,}")
    print(f"      Columnas: {list(df_bucaramanga.columns)}")


def process_delitos_informaticos() -> None:
    """
    Procesa el dataset de delitos informáticos:
        - Limpia nombres de columnas (snake_case, minúscula)
        - Ajusta nombres como codigo_municipio si aplica
        - Guarda el resultado en Silver como Parquet
    """
    print("\n" + "-" * 60)
    print("💻  PROCESANDO DELITOS INFORMÁTICOS")
    print("-" * 60)

    df_inf = load_and_clean_json(DELITOS_INF_STEM)

    if df_inf.empty:
        print("   ⚠ Dataset de delitos informáticos vacío.")
        return

    ensure_folder(SILVER_DIR)
    output_path = SILVER_DIR / DELITOS_INF_OUTPUT

    df_inf.to_parquet(output_path, engine="fastparquet", index=False)

    print(f"\n   ✅ Delitos informáticos guardado en: {output_path}")
    print(f"      Registros: {len(df_inf):,}")
    print(f"      Columnas: {list(df_inf.columns)}")


# =========================================================
# main
# =========================================================

def main() -> None:
    """Función principal del script."""
    print("=" * 60)
    print("02 - SOCRATA (BUCARAMANGA + DELITOS INFORMÁTICOS) → SILVER")
    print("=" * 60)

    process_bucaramanga()
    process_delitos_informaticos()

    print("\n" + "=" * 60)
    print("✔ Proceso de conversión y limpieza completado")
    print("=" * 60)


if __name__ == "__main__":
    main()
