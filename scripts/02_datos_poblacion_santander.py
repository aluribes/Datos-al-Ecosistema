from pathlib import Path

import pandas as pd
import re

# 1. Configuracion de rutas
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Entrada
INPUT_POB_2005 = BASE_DIR / "data" / "bronze" / "poblacion_dane" / "TerriData_Pob_2005.txt"
INPUT_POB_2018 = BASE_DIR / "data" / "bronze" / "poblacion_dane" / "TerriData_Pob_2018.txt"
INPUT_SEPARATOR = "|"
DEPARTAMENTO_FILTRO = "Santander"

# Salida
OUTPUT_DIR = BASE_DIR / "data" / "silver" / "poblacion"
OUTPUT_FILE = OUTPUT_DIR / "poblacion_santander.parquet"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 2. Cargar archivo TXT
print("Cargando archivo Censo 2005...")
poblacion_2005 = pd.read_csv(INPUT_POB_2005, sep=INPUT_SEPARATOR, dtype=str)
print("Cargando archivo Censo 2018...")
poblacion_2018 = pd.read_csv(INPUT_POB_2018, sep=INPUT_SEPARATOR, dtype=str)

# 3. Funcion de limpieza
def limpiar_df(df):
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
    def extraer_edad_min(texto):
        edades = re.findall(r"\d+", texto)
        return int(edades[0]) if edades else None

    df["edad_min"] = df["edad"].apply(extraer_edad_min)

    # Clasificar edad
    def clasificar_edad(e):
        if e is None:
            return None
        if e <= 11:
            return "MENORES"
        elif 12 <= e <= 17:
            return "ADOLESCENTES"
        return "ADULTOS"

    df["grupo_edad"] = df["edad_min"].apply(clasificar_edad)

    return df


# 4. Procesar dataset 2018
print(f"Filtrando datos del departamento '{DEPARTAMENTO_FILTRO}'...")

pob18_filtrado = poblacion_2018[poblacion_2018["Departamento"] == DEPARTAMENTO_FILTRO].copy()
pob18_filtrado = limpiar_df(pob18_filtrado)

# 5. Procesar dataset 2005
print("Filtrando datos del Censo para Santander (2010–2017)...")

pob05_filtrado = poblacion_2005[
    (poblacion_2005["Departamento"] == DEPARTAMENTO_FILTRO) &
    (poblacion_2005["Año"].astype(int).between(2010, 2017))
].copy()

pob05_filtrado = limpiar_df(pob05_filtrado)

# 6. Concatenar datasets
print("Concatenando datasets...")
poblacion_total = pd.concat([pob18_filtrado, pob05_filtrado], ignore_index=True)

# 7. Agregación final
print("Agregando datos por municipio, año, género y grupo de edad...")
pob_agg = (
    poblacion_total.groupby(
        ["codigo_municipio", "anio", "genero", "grupo_edad"]
    )["n_poblacion"]
    .sum()
    .reset_index()
)

# 8. Exportar a parquet
print("Exportando datos agregados a archivo parquet...")
pob_agg.to_parquet(OUTPUT_FILE, index=False)

print("\nArchivo parquet generado correctamente en:")
print(OUTPUT_FILE)
