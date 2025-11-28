"""
02_socrata_bucaramanga_to_parquet.py
====================================

Convierte y limpia archivos JSON de Socrata a Parquet para la capa Silver.

Entrada (Bronze):
    data/bronze/socrata_api/bucaramanga_delictiva_150.json
    data/bronze/socrata_api/bucaramanga_delitos_40.json
    data/bronze/socrata_api/delitos_informaticos.json

Salida (Silver):
    data/silver/socrata_api/delitos_bucaramanga.parquet        # Bucaramanga unificado y limpio
    data/silver/socrata_api/delitos_informaticos.parquet       # Delitos informáticos limpio

Transformaciones principales:
    - Columnas en minúscula y formato snake_case (nombre_columna)
    - Normalización de nombres de columnas para alinearlos con otros datasets:
        * cod_mun, cod_muni, cod_mpio, codigo_mun, codigo_dane_municipio -> codigo_municipio
    - Bucaramanga:
        * Limpieza específica para:
            - 40Delitos ocurridos en el Municipio de Bucaramanga
            - 150 Información delictiva del municipio de Bucaramanga
        * Unificación de ambas bases y eliminación de duplicados
        * Deducción de campos faltantes (p.ej. fecha a partir de año/mes/día)
    - Delitos informáticos:
        * fecha_hecho -> fecha (normalizada)
        * cod_depto -> codigo_departamento
"""

from __future__ import annotations

import re
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

BUCARAMANGA_OUTPUT = "delitos_bucaramanga.parquet"
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
        "COD_MUN"         -> "cod_mun"
        "Cod Mun"         -> "cod_mun"
        "Código Municipio" -> "código_municipio"

    (No elimina tildes, solo formatea.)
    """
    text = str(name).strip()
    for sep in [" ", "-", "/", "."]:
        text = text.replace(sep, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.lower()


def normalize_date(df: pd.DataFrame, date_col: str) -> pd.Series:
    """
    Normaliza fechas manejando múltiples formatos.

    Formatos soportados:
        - DD/MM/YYYY (ej: 10/10/2012)
        - YYYY-MM-DDTHH:MM:SS.sss (ej: 2003-01-03T00:00:00.000)
    """
    return pd.to_datetime(df[date_col], format="mixed", dayfirst=True, errors="coerce")


def clean_latlon(series: pd.Series, is_lat: bool) -> pd.Series:
    """
    Limpia columnas de latitud/longitud:
        - Intenta convertir a float
        - Sustituye comas por puntos
        - Valores fuera de rango se ponen como null
    """
    s = (
        series.astype(str)
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "NaN": pd.NA})
    )
    s = pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")

    if is_lat:
        mask_valid = (s >= -90) & (s <= 90)
    else:
        mask_valid = (s >= -180) & (s <= 180)

    s = s.where(mask_valid)
    return s


def extract_articulo(text: str | float | int | None) -> str | None:
    """
    Extrae la parte 'ARTICULO XX' de una descripción tipo:
        'ARTICULO 123. DESCRIPCION...'
    """
    if not isinstance(text, str):
        return None

    t = text.strip().upper()
    match = re.match(r"(ARTICULO\s+\d+)", t)
    if match:
        return match.group(1)
    return None


def extract_conducta(text: str | float | int | None) -> str | None:
    """
    Extrae la descripción de la conducta desde un texto:
        'ARTICULO 123. DESCRIPCION...' -> 'DESCRIPCION...'
    """
    if not isinstance(text, str):
        return None

    t = text.strip()
    # Buscar 'ARTICULO XX. ' y quedarse con lo que viene después
    match = re.match(r"(?i)ARTICULO\s+\d+\.\s*(.*)", t)
    if match:
        return match.group(1).strip()
    return t if t else None


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza los nombres de columnas:
        - minúscula
        - snake_case
        - mapea columnas específicas a nombres estándar del modelo
          (p.ej. codigo_municipio)
    """
    df = df.copy()

    # 1. snake_case genérico
    new_cols = {col: to_snake_case(col) for col in df.columns}
    df = df.rename(columns=new_cols)

    # 2. Mapeo específico para alinearse con otros datasets
    rename_map = {
        "cod_mun": "codigo_municipio",
        "cod_muni": "codigo_municipio",
        "cod_mpio": "codigo_municipio",
        "codigo_mun": "codigo_municipio",
        "codigo_dane_municipio": "codigo_municipio",
        "cod_municipio": "codigo_municipio",
    }

    df = df.rename(
        columns={old: new for old, new in rename_map.items() if old in df.columns},
    )

    return df


# =========================================================
# Carga y limpieza base de JSON
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
# Transformaciones específicas Bucaramanga
# =========================================================

def parse_month_label(value) -> int | None:
    """
    Convierte un valor tipo '01. ENERO' o 'ENERO' a número de mes.
    """
    if pd.isna(value):
        return None

    s = str(value).strip().upper()

    # Intentar extraer números al inicio
    match = re.match(r"(\d+)", s)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    # Si no hay número claro, usar nombre del mes
    parts = s.split(".")
    name = parts[-1].strip()

    month_map = {
        "ENERO": 1,
        "FEBRERO": 2,
        "MARZO": 3,
        "ABRIL": 4,
        "MAYO": 5,
        "JUNIO": 6,
        "JULIO": 7,
        "AGOSTO": 8,
        "SEPTIEMBRE": 9,
        "SETIEMBRE": 9,
        "OCTUBRE": 10,
        "NOVIEMBRE": 11,
        "DICIEMBRE": 12,
    }

    return month_map.get(name)


def split_day_of_week(value) -> tuple[int | None, str | None]:
    """
    Convierte un valor tipo '05. VIERNES' en:
        (5, 'VIERNES')
    """
    if pd.isna(value):
        return None, None

    s = str(value).strip()

    # Buscar 'numero - texto'
    match = re.match(r"(\d+)\D+(.*)", s)
    if not match:
        return None, s.strip().upper() if s else None

    num = match.group(1)
    name = match.group(2).strip().upper() if match.group(2) else None

    try:
        num_int = int(num)
    except ValueError:
        num_int = None

    return num_int, name


def transform_bucaramanga_40(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza específica para:
        40Delitos ocurridos en el Municipio de Bucaramanga.
    """
    df = df.copy()

    # 1) Renombrar columnas
    rename_map = {}
    if "ano" in df.columns:
        rename_map["ano"] = "anio"
    if "clasificaciones_delito" in df.columns:
        rename_map["clasificaciones_delito"] = "delito"
    if "nom_columna" in df.columns:
        rename_map["nom_columna"] = "localidad"

    df = df.rename(columns=rename_map)

    # 2) Mes en texto -> numérico
    if "mes" in df.columns:
        df["mes"] = df["mes"].apply(parse_month_label).astype("Int64")

    # 3) dia_semana -> dia_nombre, dia_nombre_orden
    if "dia_semana" in df.columns:
        dias_orden: list[int | None] = []
        dias_nombre: list[str | None] = []

        for val in df["dia_semana"]:
            orden, nombre = split_day_of_week(val)
            dias_orden.append(orden)
            dias_nombre.append(nombre)

        df["dia_nombre_orden"] = pd.Series(dias_orden, index=df.index).astype("Int64")
        df["dia_nombre"] = dias_nombre

        df = df.drop(columns=["dia_semana"])

    # 4) Eliminar columna orden si existe
    if "orden" in df.columns:
        df = df.drop(columns=["orden"])

    # 5) Validar latitud/longitud
    if "latitud" in df.columns:
        df["latitud"] = clean_latlon(df["latitud"], is_lat=True)
    if "longitud" in df.columns:
        df["longitud"] = clean_latlon(df["longitud"], is_lat=False)

    # 6) Nueva columna articulo desde descripcion_conducta
    if "descripcion_conducta" in df.columns:
        df["articulo"] = df["descripcion_conducta"].apply(extract_articulo)

    return df


def transform_bucaramanga_150(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza específica para:
        150 Información delictiva del municipio de Bucaramanga.
    """
    df = df.copy()

    # 1) Renombrar columnas
    rename_map = {}

    # año_num puede tener tilde o no según la fuente
    if "a_o_num" in df.columns:
        rename_map["a_o_num"] = "anio"
    if "ano_num" in df.columns:
        rename_map["ano_num"] = "anio"

    if "mes_num" in df.columns:
        rename_map["mes_num"] = "mes"
    if "dia_num" in df.columns:
        rename_map["dia_num"] = "dia"
    if "sexo" in df.columns:
        rename_map["sexo"] = "genero"
    if "delito_solo" in df.columns:
        rename_map["delito_solo"] = "delito"
    if "cantidad_unica" in df.columns:
        rename_map["cantidad_unica"] = "cantidad"
    if "fecha_hecho" in df.columns:
        rename_map["fecha_hecho"] = "fecha"
    if "hora_hecho" in df.columns:
        rename_map["hora_hecho"] = "hora"

    df = df.rename(columns=rename_map)

    # 2) dia_nombre en mayúsculas
    if "dia_nombre" in df.columns:
        df["dia_nombre"] = (
            df["dia_nombre"]
            .astype(str)
            .str.strip()
            .replace({"": pd.NA})
            .str.upper()
        )

    # 3) descripcion_conducta -> conducta + articulo
    if "descripcion_conducta" in df.columns:
        df["conducta"] = df["descripcion_conducta"].apply(extract_conducta)
        df["articulo"] = df["descripcion_conducta"].apply(extract_articulo)

    # 4) edad "NO DISPONIBLE" -> null
    if "edad" in df.columns:
        df["edad"] = (
            df["edad"]
            .replace("NO DISPONIBLE", pd.NA)
            .replace("", pd.NA)
        )
        edad_num = pd.to_numeric(df["edad"], errors="coerce")

        # 5) curso_de_vida desde edad
        def map_curso_vida(age: float | int | None) -> str:
            if pd.isna(age):
                return "NO REPORTA"
            age_int = int(age)
            if 0 <= age_int <= 6:
                return "01. PRIMERA INFANCIA"
            if 7 <= age_int <= 11:
                return "02. INFANCIA"
            if 12 <= age_int <= 18:
                return "03. ADOLESCENCIA"
            if 19 <= age_int <= 28:
                return "04. JOVENES"
            if 29 <= age_int <= 59:
                return "05. ADULTEZ"
            if age_int >= 60:
                return "06. PERSONA MAYOR"
            return "NO REPORTA"

        df["curso_de_vida"] = edad_num.apply(map_curso_vida)

    # 6) Eliminar columnas curso_vida y curso_vida_orden si existen
    cols_to_drop = [c for c in ["curso_vida", "curso_vida_orden"] if c in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # 7) Formatear fecha y hora
    if "fecha" in df.columns:
        df["fecha"] = normalize_date(df, "fecha")

    if "hora" in df.columns:
        # Normalizar a strings HH:MM:SS, valores inválidos -> <NA>
        hora_raw = (
            df["hora"]
            .astype(str)
            .str.strip()
            .replace({"": pd.NA, "NaT": pd.NA, "nan": pd.NA})
        )

        dt = pd.to_datetime(
            "1970-01-01 " + hora_raw.astype(str),
            errors="coerce",
        )

        hora_out = dt.dt.strftime("%H:%M:%S")
        # Donde la conversión falló, dejamos como <NA>
        hora_out = hora_out.where(dt.notna(), pd.NA)
        df["hora"] = hora_out.astype("string")

    return df


# =========================================================
# Procesos específicos
# =========================================================

def process_bucaramanga() -> None:
    """
    Procesa los dos datasets de Bucaramanga:

        - bucaramanga_delictiva_150
        - bucaramanga_delitos_40

    Aplica limpiezas específicas, unifica ambos en un solo DataFrame,
    intenta deducir información faltante (p.ej. fecha) y elimina duplicados.
    Guarda el resultado en Silver como Parquet.
    """
    print("\n" + "-" * 60)
    print("🏙  PROCESANDO BUCARAMANGA (UNIFICAR + LIMPIAR)")
    print("-" * 60)

    dataframes: list[pd.DataFrame] = []

    for stem in BUCARAMANGA_STEMS:
        df_stem = load_and_clean_json(stem)

        if stem == "bucaramanga_delitos_40":
            df_stem = transform_bucaramanga_40(df_stem)
        elif stem == "bucaramanga_delictiva_150":
            df_stem = transform_bucaramanga_150(df_stem)

        if df_stem.empty:
            print(f"   ⚠ Dataset vacío después de limpieza: {stem}")
        else:
            print(f"   ✔ Dataset {stem} con {len(df_stem):,} filas tras limpieza")
            dataframes.append(df_stem)

    if not dataframes:
        print("   ❌ No hay datos de Bucaramanga para procesar.")
        return

    # Unificar
    df_bucaramanga = pd.concat(dataframes, ignore_index=True, sort=False)

    # Intentar deducir fecha a partir de (anio, mes, dia) cuando falte
    if {"anio", "mes", "dia"}.issubset(df_bucaramanga.columns):
        if "fecha" not in df_bucaramanga.columns:
            df_bucaramanga["fecha"] = pd.NaT

        mask_missing_fecha = df_bucaramanga["fecha"].isna()
        if mask_missing_fecha.any():
            try:
                fecha_from_parts = pd.to_datetime(
                    {
                        "year": df_bucaramanga.loc[mask_missing_fecha, "anio"],
                        "month": df_bucaramanga.loc[mask_missing_fecha, "mes"],
                        "day": df_bucaramanga.loc[mask_missing_fecha, "dia"],
                    },
                    errors="coerce",
                )
                df_bucaramanga.loc[mask_missing_fecha, "fecha"] = fecha_from_parts
            except Exception as exc:  # noqa: BLE001
                print(f"   ⚠ No se pudo reconstruir fecha desde año/mes/día: {exc}")

    # Deducir articulo donde esté null y exista descripcion_conducta
    if "articulo" in df_bucaramanga.columns and "descripcion_conducta" in df_bucaramanga.columns:
        mask_null_art = df_bucaramanga["articulo"].isna()
        if mask_null_art.any():
            df_bucaramanga.loc[mask_null_art, "articulo"] = (
                df_bucaramanga.loc[mask_null_art, "descripcion_conducta"]
                .apply(extract_articulo)
            )

    # Eliminar duplicados
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
        - Renombra fecha_hecho -> fecha y la normaliza
        - Renombra cod_depto -> codigo_departamento
        - Guarda el resultado en Silver como Parquet
    """
    print("\n" + "-" * 60)
    print("💻  PROCESANDO DELITOS INFORMÁTICOS")
    print("-" * 60)

    df_inf = load_and_clean_json(DELITOS_INF_STEM)

    if df_inf.empty:
        print("   ⚠ Dataset de delitos informáticos vacío.")
        return

    # Renombrar columnas específicas
    rename_map: dict[str, str] = {}
    if "fecha_hecho" in df_inf.columns:
        rename_map["fecha_hecho"] = "fecha"
    if "cod_depto" in df_inf.columns:
        rename_map["cod_depto"] = "codigo_departamento"

    if rename_map:
        df_inf = df_inf.rename(columns=rename_map)

    # Normalizar fecha
    if "fecha" in df_inf.columns:
        df_inf["fecha"] = normalize_date(df_inf, "fecha")

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
