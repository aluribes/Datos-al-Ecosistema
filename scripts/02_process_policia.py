import pandas as pd
from pathlib import Path
from typing import List

# Rutas y configuración
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

BRONZE_POLICIA_DIR = BASE_DIR / "data" / "bronze" / "policia_scraping"
SILVER_POLICIA_DIR = BASE_DIR / "data" / "silver" / "policia_scraping"
SILVER_POLICIA_FILENAME = "policia_santander.parquet"


# Funciones auxiliares

def detectar_fila_encabezado(
    preview_df: pd.DataFrame,
    min_idx: int = 9,
    max_idx: int = 12
) -> int:
    """
    Detecta la fila de encabezado en un DataFrame de previsualización,
    asumiendo que los posibles encabezados están entre min_idx y max_idx (0-based),
    escogiendo la fila con más valores no nulos.
    """
    max_idx = min(max_idx, len(preview_df) - 1)
    min_idx = max(min_idx, 0)

    if min_idx > max_idx:
        return 0

    mejor_fila = min_idx
    mejor_conteo = -1

    for i in range(min_idx, max_idx + 1):
        row = preview_df.iloc[i]
        conteo_no_nulos = row.notna().sum()
        if conteo_no_nulos > mejor_conteo:
            mejor_conteo = conteo_no_nulos
            mejor_fila = i

    return mejor_fila


def leer_archivo_policia(path: Path) -> pd.DataFrame:
    """
    Lee un archivo Excel de la policía (xls/xlsx), detectando la fila de encabezados
    entre los índices 9 y 12, limpiando filas vacías y añadiendo metadatos:
    - anio
    - delito_archivo
    - archivo_origen
    """
    print(f"\nProcesando: {path.name} ...")

    # 1) Previsualizar el archivo sin encabezado
    preview = pd.read_excel(path, header=None, nrows=20)

    # 2) Detectar la fila de encabezado
    header_row = detectar_fila_encabezado(preview, min_idx=9, max_idx=12)
    print(f"  -> Fila de encabezado detectada (index): {header_row}")

    # 3) Leer el archivo completo sin encabezado
    raw = pd.read_excel(path, header=None)

    # 4) Separar encabezados y datos
    header = raw.iloc[header_row]
    df_archivo = raw.iloc[header_row + 1 :].copy()

    # 5) Asignar encabezados
    df_archivo.columns = header

    # 6) Eliminar columnas cuyo encabezado sea NaN
    df_archivo = df_archivo.loc[:, df_archivo.columns.notna()]

    # 7) Eliminar filas completamente vacías
    df_archivo = df_archivo.dropna(how="all")

    # 8) Normalizar nombres de columnas
    df_archivo.columns = df_archivo.columns.astype(str).str.strip()

    # 9) Extraer metadatos desde el nombre de archivo
    stem = path.stem  # nombre sin extensión
    partes = stem.split("_")

    # Año: primer token de 4 dígitos
    anio = None
    for p in partes:
        if p.isdigit() and len(p) == 4:
            anio = int(p)
            break

    # Delito (desde nombre del archivo): primer token no numérico
    delito_archivo = None
    for p in partes:
        if not p.isdigit():
            delito_archivo = p
            break

    df_archivo["anio"] = anio
    df_archivo["delito_archivo"] = delito_archivo
    df_archivo["archivo_origen"] = path.name

    return df_archivo


def unificar_archivos_policia(bronze_dir: Path) -> pd.DataFrame:
    """
    Une todos los archivos .xls y .xlsx de la carpeta de policía scraping
    en un único DataFrame.
    """
    archivos: List[Path] = sorted(
        list(bronze_dir.glob("*.xlsx")) +
        list(bronze_dir.glob("*.xls"))
    )

    print(f"Encontrados {len(archivos)} archivos de policía (xls + xlsx).")

    dfs = []
    for path in archivos:
        try:
            df_archivo = leer_archivo_policia(path)
            dfs.append(df_archivo)
        except Exception as e:
            print(f"⚠️ Error procesando {path.name}: {e}")

    if not dfs:
        print("No se logró cargar ningún archivo de policía.")
        return pd.DataFrame()

    df_unificado = pd.concat(dfs, ignore_index=True, sort=False)
    print("\nUnificación completa.")
    print(f"Filas totales: {len(df_unificado)}")

    return df_unificado


def combinar_columnas(df: pd.DataFrame, columnas_origen: List[str], nombre_destino: str) -> pd.DataFrame:
    """
    Combina varias columnas similares en una sola, tomando el primer valor no nulo.
    Solo usa las columnas que existan en el DataFrame.
    """
    cols_existentes = [c for c in columnas_origen if c in df.columns]
    if not cols_existentes:
        return df

    df[nombre_destino] = df[cols_existentes].bfill(axis=1).iloc[:, 0]
    return df


def crear_df_limpio_desde_unificado(df_unificado: pd.DataFrame) -> pd.DataFrame:
    """
    A partir de df_policia_unificado, crea df_policia_unificado_limpio con
    columnas homogéneas y nombres estandarizados.
    """
    df = df_unificado.copy()

    # Definición de grupos de columnas equivalentes
    edad_cols = [
        "*AGRUPA EDAD PERSONA",
        "*AGRUPA EDAD PERSONA*",
        "*AGRUPA_EDAD_PERSONA",
        "AGRUPA EDAD PERSONA",
        "AGRUPA_EDAD_PERSONA",
        "GRUPO ETARIO",
    ]

    armas_cols = [
        "ARMA MEDIO",
        "ARMAS MEDIO",
        "ARMAS MEDIOS",
        "ARMAS_MEDIOS",
    ]

    codigo_dane_cols = [
        "CODIGO DANE",
        "CODIGO_DANE",
    ]

    delito_cols = [
        "DELITO",
        "DELITOS",
    ]

    departamento_cols = [
        "DEPARTAMENTO",
        "Departamento",
    ]

    fecha_cols = [
        "FECHA",
        "FECHA  HECHO",
        "FECHA HECHO",
    ]

    municipio_cols = [
        "MUNICICPIO",
        "MUNICIPIO",
        "MUNICIPO",
        "Municipio",
    ]

    descripcion_col = "DESCRIPCION CONDUCTA"
    genero_col = "GENERO"
    cantidad_col = "CANTIDAD"

    # Combinar columnas en nuevas columnas limpias
    df = combinar_columnas(df, edad_cols, "edad_persona")
    df = combinar_columnas(df, armas_cols, "armas_medios")
    df = combinar_columnas(df, codigo_dane_cols, "codigo_dane")
    df = combinar_columnas(df, delito_cols, "delito")
    df = combinar_columnas(df, departamento_cols, "departamento")
    df = combinar_columnas(df, fecha_cols, "fecha")
    df = combinar_columnas(df, municipio_cols, "municipio")

    if descripcion_col in df.columns:
        df["descripcion_conducta"] = df[descripcion_col]
    if genero_col in df.columns:
        df["genero"] = df[genero_col]
    if cantidad_col in df.columns:
        df["cantidad"] = df[cantidad_col]

    # Columnas finales que nos interesa conservar
    columnas_finales = [
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

    columnas_finales_existentes = [c for c in columnas_finales if c in df.columns]
    df_limpio = df[columnas_finales_existentes].copy()

    # Normalizar departamento a mayúsculas
    if "departamento" in df_limpio.columns:
        df_limpio["departamento"] = (
            df_limpio["departamento"].astype(str).str.strip().str.upper()
        )

    return df_limpio


def limpiar_y_filtrar_santander(df_limpio: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas las transformaciones de limpieza sobre df_limpio y
    devuelve df_policia_santander listo para exportar.
    """
    df = df_limpio.copy()

    # Filtrar solo SANTANDER
    df = df[df["departamento"] == "SANTANDER"].copy()

    # Correcciones a delito_archivo
    reemplazos_delito_archivo = {
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
        df["delito_archivo"] = df["delito_archivo"].replace(reemplazos_delito_archivo)

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

        valores_no_reportado = [
            "",
            "-",
            "NO REPORTA",
            "NO REPORTADO",
            "NO RESPORTADO",
        ]

        df["edad_persona"] = (
            df["edad_persona"].replace(valores_no_reportado, "NO REPORTADO")
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
        mask_notna_armas = df["armas_medios"].notna()
        df.loc[mask_notna_armas, "armas_medios"] = (
            df.loc[mask_notna_armas, "armas_medios"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        valores_no_reportado_armas = [
            "-",
            "NO REPORTA",
            "NO REPORTADO",
            "NO RESPORTADO",
        ]

        df["armas_medios"] = (
            df["armas_medios"].replace(valores_no_reportado_armas, "NO REPORTADO")
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


def preparar_para_exportar(df_policia_santander: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte tipos problemáticos antes de exportar:
    - fecha a datetime (dayfirst)
    - codigo_dane a string (si existe)
    """
    df = df_policia_santander.copy()

    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(
            df["fecha"],
            errors="coerce",
            dayfirst=True,
        )

    if "codigo_dane" in df.columns:
        df["codigo_dane"] = df["codigo_dane"].astype(str).str.strip()

    return df


def exportar_a_parquet(df_policia_santander: pd.DataFrame, silver_dir: Path, filename: str) -> None:
    """
    Exporta df_policia_santander a un archivo Parquet en la ruta Silver.
    """
    silver_dir.mkdir(parents=True, exist_ok=True)
    output_path = silver_dir / filename

    df_policia_santander.to_parquet(
        output_path,
        engine="fastparquet",
        index=False,
    )

    print(f"Archivo guardado en: {output_path}")


# main

def main() -> None:
    # 1) Unificar todos los archivos de policía (Bronze)
    df_unificado = unificar_archivos_policia(BRONZE_POLICIA_DIR)

    if df_unificado.empty:
        print("No hay datos para procesar.")
        return

    # 2) Crear dataframe limpio con columnas homogéneas
    df_limpio = crear_df_limpio_desde_unificado(df_unificado)

    # 3) Limpiar y filtrar para Santander
    df_policia_santander = limpiar_y_filtrar_santander(df_limpio)

    # 4) Ajustar tipos para exportar (fecha, codigo_dane)
    df_policia_santander = preparar_para_exportar(df_policia_santander)

    # 5) Exportar a Silver
    exportar_a_parquet(df_policia_santander, SILVER_POLICIA_DIR, SILVER_POLICIA_FILENAME)


if __name__ == "__main__":
    main()
