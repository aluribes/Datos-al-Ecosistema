"""
02_process_policia_completo.py
==============================

Procesa datos de la Policía Nacional para la capa Silver (todos los departamentos).

Entrada:
    data/bronze/policia_scraping/*.xlsx

Salida:
    data/silver/policia_scraping/policia_completo.parquet
"""

from pathlib import Path
from typing import List

import pandas as pd

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

BRONZE_POLICE_DIR = BASE_DIR / "data" / "bronze" / "policia_scraping"
SILVER_POLICE_DIR = BASE_DIR / "data" / "silver" / "policia_scraping"
SILVER_POLICE_FILENAME = "policia_completo.parquet"


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


def normalize_cod_muni(value) -> str:
    """
    Normaliza el código de municipio a 5 dígitos.

    Ejemplos:
        "68755000" -> "68755"
        "68001" -> "68001"
        68755 -> "68755"
    """
    if pd.isna(value):
        return "00000"

    # Convertir a string y limpiar
    code = str(value).strip()

    # Remover decimales si existen (ej: "68755.0")
    if "." in code:
        code = code.split(".")[0]

    # Si tiene más de 5 dígitos, tomar los primeros 5
    if len(code) > 5:
        code = code[:5]

    # Asegurar que tenga 5 dígitos (padding con ceros a la izquierda)
    return code.zfill(5)


def normalize_date(df: pd.DataFrame, date_col: str) -> pd.Series:
    """
    Normaliza fechas manejando múltiples formatos.

    Formatos soportados:
        - DD/MM/YYYY (ej: 10/10/2012)
        - YYYY-MM-DDTHH:MM:SS.sss (ej: 2003-01-03T00:00:00.000)
    """
    return pd.to_datetime(df[date_col], format="mixed", dayfirst=True, errors="coerce")


# =========================================================
# Lectura y unificación de archivos de Policía
# =========================================================

def detect_header_row(
    df: pd.DataFrame,
    min_idx: int = 9,
    max_idx: int = 12,
) -> int:
    """
    Detecta la fila de encabezado en un DataFrame,
    asumiendo que los posibles encabezados están entre min_idx y max_idx (0-based),
    escogiendo la fila con más valores no nulos.
    """
    max_idx = min(max_idx, len(df) - 1)
    min_idx = max(min_idx, 0)

    if min_idx > max_idx:
        return 0

    best_row = min_idx
    best_count = -1

    for i in range(min_idx, max_idx + 1):
        count_not_null = df.iloc[i].notna().sum()
        if count_not_null > best_count:
            best_count = count_not_null
            best_row = i

    return best_row


def load_police_file(path: Path) -> pd.DataFrame:
    """
    Lee un archivo Excel de la policía (xls/xlsx), detectando la fila de encabezados
    entre los índices 9 y 12, limpiando filas vacías y añadiendo metadatos:
        - anio
        - delito_archivo
        - archivo_origen
    """
    print(f"\n➤ Procesando archivo: {path.name}")

    # 1) Leer todo el archivo una sola vez (optimización)
    raw = pd.read_excel(path, header=None)

    # 2) Detectar la fila de encabezado en el DataFrame completo
    header_row = detect_header_row(raw, min_idx=9, max_idx=12)
    print(f"   • Fila de encabezado detectada (index): {header_row}")

    # 3) Separar encabezados y datos
    header = raw.iloc[header_row]
    df_file = raw.iloc[header_row + 1 :].copy()

    # 4) Asignar encabezados
    df_file.columns = header

    # 5) Eliminar columnas cuyo encabezado sea NaN
    df_file = df_file.loc[:, df_file.columns.notna()]

    # 6) Eliminar filas completamente vacías
    df_file = df_file.dropna(how="all")

    # 7) Normalizar nombres de columnas
    df_file.columns = df_file.columns.astype(str).str.strip()

    # 8) Extraer metadatos desde el nombre de archivo
    stem = path.stem  # nombre sin extensión
    parts = stem.split("_")

    # Año: primer token de 4 dígitos
    year = None
    for token in parts:
        if token.isdigit() and len(token) == 4:
            year = int(token)
            break

    # Delito (desde nombre del archivo): primer token no numérico
    file_crime = None
    for token in parts:
        if not token.isdigit():
            file_crime = token
            break

    df_file["anio"] = year
    df_file["delito_archivo"] = file_crime
    df_file["archivo_origen"] = path.name

    return df_file


def unify_police_files(bronze_dir: Path) -> pd.DataFrame:
    """
    Une todos los archivos .xls y .xlsx de la carpeta de policía scraping
    en un único DataFrame.
    """
    check_exists(bronze_dir, label="Carpeta Bronze Policía")

    files: List[Path] = sorted(
        list(bronze_dir.glob("*.xlsx")) + list(bronze_dir.glob("*.xls")),
    )

    print(f"\nEncontrados {len(files)} archivos de policía (xls + xlsx).")

    dataframes: list[pd.DataFrame] = []
    for path in files:
        try:
            df_file = load_police_file(path)
            dataframes.append(df_file)
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ Error procesando {path.name}: {exc}")

    if not dataframes:
        print("❌ No se logró cargar ningún archivo de policía.")
        return pd.DataFrame()

    df_unified = pd.concat(dataframes, ignore_index=True, sort=False)
    print("\n✔ Unificación completa.")
    print(f"   Filas totales unificadas: {len(df_unified):,}")

    return df_unified


# =========================================================
# Limpieza y normalización de columnas
# =========================================================

def combine_columns(
    df: pd.DataFrame,
    source_columns: List[str],
    target_name: str,
) -> pd.DataFrame:
    """
    Combina varias columnas similares en una sola, tomando el primer valor no nulo.
    Solo usa las columnas que existan en el DataFrame.
    """
    existing_cols = [col for col in source_columns if col in df.columns]
    if not existing_cols:
        return df

    df[target_name] = df[existing_cols].bfill(axis=1).iloc[:, 0]
    return df


def build_clean_dataframe(df_unified: pd.DataFrame) -> pd.DataFrame:
    """
    A partir de df_unified, crea un DataFrame limpio con
    columnas homogéneas y nombres estandarizados.
    """
    df = df_unified.copy()

    # Definición de grupos de columnas equivalentes
    age_cols = [
        "*AGRUPA EDAD PERSONA",
        "*AGRUPA EDAD PERSONA*",
        "*AGRUPA_EDAD_PERSONA",
        "AGRUPA EDAD PERSONA",
        "AGRUPA_EDAD_PERSONA",
        "GRUPO ETARIO",
    ]

    weapon_cols = [
        "ARMA MEDIO",
        "ARMAS MEDIO",
        "ARMAS MEDIOS",
        "ARMAS_MEDIOS",
    ]

    dane_code_cols = [
        "CODIGO DANE",
        "CODIGO_DANE",
    ]

    crime_cols = [
        "DELITO",
        "DELITOS",
    ]

    department_cols = [
        "DEPARTAMENTO",
        "Departamento",
    ]

    date_cols = [
        "FECHA",
        "FECHA  HECHO",
        "FECHA HECHO",
    ]

    city_cols = [
        "MUNICICPIO",
        "MUNICIPIO",
        "MUNICIPO",
        "Municipio",
    ]

    description_col = "DESCRIPCION CONDUCTA"
    gender_col = "GENERO"
    quantity_col = "CANTIDAD"

    # Combinar columnas en nuevas columnas limpias
    df = combine_columns(df, age_cols, "edad_persona")
    df = combine_columns(df, weapon_cols, "armas_medios")
    df = combine_columns(df, dane_code_cols, "codigo_dane")
    df = combine_columns(df, crime_cols, "delito")
    df = combine_columns(df, department_cols, "departamento")
    df = combine_columns(df, date_cols, "fecha")
    df = combine_columns(df, city_cols, "municipio")

    if description_col in df.columns:
        df["descripcion_conducta"] = df[description_col]

    if gender_col in df.columns:
        df["genero"] = df[gender_col]

    if quantity_col in df.columns:
        df["cantidad"] = df[quantity_col]

    # Columnas finales que nos interesa conservar
    final_columns = [
        "departamento",
        "municipio",
        "codigo_dane",
        "delito",
        "edad_persona",
        "armas_medios",
        "cantidad",
        "descripcion_conducta",
        "fecha",
        "genero",
        "anio",
        "delito_archivo",
        "archivo_origen",
    ]

    existing_final_columns = [col for col in final_columns if col in df.columns]
    df_clean = df[existing_final_columns].copy()

    # Normalizar departamento a mayúsculas (para todos los departamentos)
    if "departamento" in df_clean.columns:
        df_clean["departamento"] = (
            df_clean["departamento"].astype(str).str.strip().str.upper()
        )

    return df_clean


def clean_police_data(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas las transformaciones de limpieza sobre df_clean
    sin filtrar por departamento.
    """
    df = df_clean.copy()

    # Correcciones a delito_archivo
    replacements_file_crime = {
        "Delitos%20sexuales": "Delitos sexuales",
        "Extorsi%C3%B3n": "Extorsion",
        "Homicidio%20Intencional": "Homicidios",
        "Delitos": "Delitos sexuales",
        "Violencia%20intrafamiliar": "Violencia intrafamiliar",
        "Violencia": "Violencia intrafamiliar",
        "Lesiones%20personales": "Lesiones",
        "Lesiones": "Lesiones",
        "Lesiones%20en%20accidente%20de%20tr%C3%A1nsito": "Lesiones",
        "Hurto%20pirater%C3%ADa%20terrestre": "Hurtos",
        "Hurto%20automotores": "Hurtos",
        "Hurto%20a%20residencias": "Hurtos",
        "Hurto%20a%20personas": "Hurtos",
        "Hurto%20a%20motocicletas": "Hurtos",
        "Hurto%20a%20entidades%20Financieras": "Hurtos",
        "Hurto%20a%20comercio": "Hurtos",
        "Hurto%20a%20cabezas%20de%20ganado": "Abigeato",
        "Hurto": "Hurtos",
        "Homicidios%20en%20accidente%20de%20tr%C3%A1nsito": "Homicidios",
    }

    if "delito_archivo" in df.columns:
        df["delito_archivo"] = df["delito_archivo"].replace(replacements_file_crime)

    # Limpiar municipio y delito (si existen)
    if "municipio" in df.columns:
        df["municipio"] = (
            df["municipio"].astype(str).str.strip().str.upper()
        )

    if "delito" in df.columns:
        df["delito"] = (
            df["delito"].astype(str).str.strip().str.upper()
        )

    # Limpiar edad_persona
    if "edad_persona" in df.columns:
        df["edad_persona"] = df["edad_persona"].where(df["edad_persona"].notna())
        mask_notna = df["edad_persona"].notna()
        df.loc[mask_notna, "edad_persona"] = (
            df.loc[mask_notna, "edad_persona"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        no_report_age_values = [
            "",
            "-",
            "NO REPORTA",
            "NO REPORTADO",
            "NO RESPORTADO",
        ]

        df["edad_persona"] = df["edad_persona"].replace(
            no_report_age_values,
            "NO REPORTADO",
        )
        df["edad_persona"] = df["edad_persona"].fillna("NO REPORTADO")

        # Eliminar registros con edad_persona = NO REPORTADO
        df = df[df["edad_persona"] != "NO REPORTADO"].copy()

    # Eliminar registros con genero nulo
    if "genero" in df.columns:
        df = df[df["genero"].notna()].copy()

    # Limpiar armas_medios
    if "armas_medios" in df.columns:
        df["armas_medios"] = df["armas_medios"].where(df["armas_medios"].notna())
        mask_notna_weapon = df["armas_medios"].notna()
        df.loc[mask_notna_weapon, "armas_medios"] = (
            df.loc[mask_notna_weapon, "armas_medios"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        no_report_weapon_values = [
            "-",
            "NO REPORTA",
            "NO REPORTADO",
            "NO RESPORTADO",
        ]

        df["armas_medios"] = df["armas_medios"].replace(
            no_report_weapon_values,
            "NO REPORTADO",
        )
        df["armas_medios"] = df["armas_medios"].fillna("NO REPORTADO")

    # Si existe descripcion_conducta, ya no se usa; se elimina
    if "descripcion_conducta" in df.columns:
        df = df.drop(columns=["descripcion_conducta"])

    # Eliminar columna delito si existe (la vamos a redefinir desde delito_archivo)
    if "delito" in df.columns:
        df = df.drop(columns=["delito"])

    # Renombrar delito_archivo -> delito y poner en mayúsculas
    if "delito_archivo" in df.columns:
        df = df.rename(columns={"delito_archivo": "delito"})
        df["delito"] = (
            df["delito"].astype(str).str.strip().str.upper()
        )

    # Eliminar archivo_origen si existe
    if "archivo_origen" in df.columns:
        df = df.drop(columns=["archivo_origen"])

    # Eliminar registros donde delito sea PIRATERIA o SECUESTRO
    if "delito" in df.columns:
        df = df[~df["delito"].isin(["PIRATERIA", "SECUESTRO"])].copy()

    return df


def prepare_for_export(df_police: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte tipos problemáticos antes de exportar:
        - fecha a datetime (usando normalize_date)
        - codigo_dane a string
        - agrega codigo_municipio normalizado desde codigo_dane
        - agrega codigo_departamento = primeros 2 dígitos de codigo_municipio
    """
    df = df_police.copy()

    # Normalizar fecha
    if "fecha" in df.columns:
        df["fecha"] = normalize_date(df, "fecha")

    # Normalizar códigos DANE / municipio / departamento
    if "codigo_dane" in df.columns:
        df["codigo_dane"] = df["codigo_dane"].astype(str).str.strip()
        df["codigo_municipio"] = df["codigo_dane"].apply(normalize_cod_muni)
    else:
        df["codigo_municipio"] = "00000"

    # Código de departamento: primeros 2 dígitos del código de municipio
    df["codigo_departamento"] = df["codigo_municipio"].str[:2]

    return df


def export_to_parquet(
    df_police: pd.DataFrame,
    silver_dir: Path,
    filename: str,
) -> None:
    """
    Exporta df_police a un archivo Parquet en la ruta Silver.
    """
    ensure_folder(silver_dir)
    output_path = silver_dir / filename

    df_police.to_parquet(
        output_path,
        engine="fastparquet",
        index=False,
    )

    print(f"\n✅ Archivo guardado en: {output_path}")
    print(f"   Registros: {len(df_police):,}")
    print(f"   Columnas: {df_police.columns.tolist()}")


# =========================================================
# main
# =========================================================

def main() -> None:
    """Función principal del script."""
    print("=" * 60)
    print("02 - PROCESAMIENTO POLICÍA COMPLETO (BRONZE → SILVER)")
    print("=" * 60)

    # 1) Unificar todos los archivos de policía (Bronze)
    df_unified = unify_police_files(BRONZE_POLICE_DIR)

    if df_unified.empty:
        print("❌ No hay datos para procesar.")
        return

    # 2) Crear dataframe limpio con columnas homogéneas
    df_clean = build_clean_dataframe(df_unified)

    # 3) Limpiar datos (sin filtrar por departamento)
    df_police_clean = clean_police_data(df_clean)

    # 4) Ajustar tipos y códigos para exportar
    df_police_ready = prepare_for_export(df_police_clean)

    # 5) Exportar a Silver
    export_to_parquet(
        df_police_ready,
        SILVER_POLICE_DIR,
        SILVER_POLICE_FILENAME,
    )

    print("=" * 60)
    print("✔ Proceso Policía COMPLETO → Silver completado")
    print("=" * 60)


if __name__ == "__main__":
    main()