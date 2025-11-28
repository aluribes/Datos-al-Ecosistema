"""
02_datos_poblacion_santander.py
================================

Procesa datos de población del DANE para la capa Silver.

Entrada:
    data/bronze/poblacion_dane/TerriData_Pob_2005.rar (contiene TerriData_Pob_2005.txt)
    data/bronze/poblacion_dane/TerriData_Pob_2018.rar (contiene TerriData_Pob_2018.txt)

Salida:
    data/silver/poblacion/poblacion_santander.parquet
"""

from pathlib import Path
import re

import pandas as pd
import rarfile

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Entrada (archivos RAR comprimidos)
INPUT_POB_2005_RAR = BASE_DIR / "data" / "bronze" / "poblacion_dane" / "TerriData_Pob_2005.rar"
INPUT_POB_2018_RAR = BASE_DIR / "data" / "bronze" / "poblacion_dane" / "TerriData_Pob_2018.rar"
# Nombres de los archivos TXT dentro de los RAR
ARCHIVO_INTERNO_2005 = "TerriData_Pob_2005.txt"
ARCHIVO_INTERNO_2018 = "TerriData_Pob_2018.txt"
INPUT_SEPARATOR = "|"
DEPARTAMENTO_FILTRO = "Santander"

# Salida
OUTPUT_DIR = BASE_DIR / "data" / "silver" / "poblacion"
OUTPUT_FILE = OUTPUT_DIR / "poblacion_santander.parquet"


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def load_poblacion_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga los archivos de población del DANE desde archivos RAR comprimidos."""
    print("Cargando archivo Censo 2005 desde RAR...")
    with rarfile.RarFile(INPUT_POB_2005_RAR, 'r') as rf:
        with rf.open(ARCHIVO_INTERNO_2005) as f:
            poblacion_2005 = pd.read_csv(f, sep=INPUT_SEPARATOR, dtype=str)
    
    print("Cargando archivo Censo 2018 desde RAR...")
    with rarfile.RarFile(INPUT_POB_2018_RAR, 'r') as rf:
        with rf.open(ARCHIVO_INTERNO_2018) as f:
            poblacion_2018 = pd.read_csv(f, sep=INPUT_SEPARATOR, dtype=str)
    
    return poblacion_2005, poblacion_2018


def limpiar_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y transforma el DataFrame de población.
    
    Incluye:
        - Renombrado de columnas
        - Conversión de tipos
        - Clasificación de edades
        - Estandarización de género
    """
    # Renombrar
    df = df.rename(columns={
        "Código Entidad": "codigo_municipio",
        "Entidad": "municipio",
        "Departamento": "departamento",
        "Año": "anio",
        "Mes": "mes",
        "Dato Numérico": "n_poblacion",
        "Indicador": "edad",
        "Unidad de Medida": "genero"
    })

    # Números
    df["n_poblacion"] = (
        df["n_poblacion"]
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
            .round()
            .astype(int)
    )

    # Género
    df["genero"] = (
        df["genero"]
            .fillna("")
            .str.lower()
            .apply(lambda x: "MASCULINO" if "hombre" in x else
                             "FEMENINO" if "mujer" in x else None)
    )

    # Eliminar porcentajes
    df = df[~df["edad"].str.contains("Porcentaje", case=False, na=False)]

    # Extraer edad mínima
    def extraer_edad_min(texto: str) -> int | None:
        edades = re.findall(r"\d+", texto)
        return int(edades[0]) if edades else None

    df["edad_min"] = df["edad"].apply(extraer_edad_min)

    # Clasificar edad
    def clasificar_edad(e: int | None) -> str | None:
        if e is None:
            return None
        if e <= 11:
            return "MENORES"
        elif 12 <= e <= 17:
            return "ADOLESCENTES"
        return "ADULTOS"

    df["grupo_edad"] = df["edad_min"].apply(clasificar_edad)

    return df


def process_poblacion(
    poblacion_2005: pd.DataFrame, 
    poblacion_2018: pd.DataFrame
) -> pd.DataFrame:
    """
    Procesa y combina los datasets de población.
    
    Args:
        poblacion_2005: DataFrame del censo 2005
        poblacion_2018: DataFrame del censo 2018
        
    Returns:
        DataFrame agregado por municipio, año, género y grupo de edad
    """
    print(f"Filtrando datos del departamento '{DEPARTAMENTO_FILTRO}'...")
    
    # Procesar dataset 2018
    pob18_filtrado = poblacion_2018[
        poblacion_2018["Departamento"] == DEPARTAMENTO_FILTRO
    ].copy()
    pob18_filtrado = limpiar_df(pob18_filtrado)
    
    # Procesar dataset 2005 (años 2010-2017)
    print("Filtrando datos del Censo para Santander (2010–2017)...")
    pob05_filtrado = poblacion_2005[
        (poblacion_2005["Departamento"] == DEPARTAMENTO_FILTRO) &
        (poblacion_2005["Año"].astype(int).between(2010, 2017))
    ].copy()
    pob05_filtrado = limpiar_df(pob05_filtrado)
    
    # Concatenar datasets
    print("Concatenando datasets...")
    poblacion_total = pd.concat([pob18_filtrado, pob05_filtrado], ignore_index=True)
    
    # Agregación final
    print("Agregando datos por municipio, año, género y grupo de edad...")
    pob_agg = (
        poblacion_total.groupby(
            ["codigo_municipio", "anio", "genero", "grupo_edad"]
        )["n_poblacion"]
        .sum()
        .reset_index()
    )
    
    return pob_agg


def main() -> None:
    """Función principal del script."""
    ensure_folder(OUTPUT_DIR)
    
    # Cargar datos
    poblacion_2005, poblacion_2018 = load_poblacion_data()
    
    # Procesar
    pob_agg = process_poblacion(poblacion_2005, poblacion_2018)
    
    # Exportar
    print("Exportando datos agregados a archivo parquet...")
    pob_agg.to_parquet(OUTPUT_FILE, index=False)
    
    print(f"\n✔ Archivo parquet generado correctamente en:\n{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
