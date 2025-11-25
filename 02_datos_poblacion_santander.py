import pandas as pd
import os
import re

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ruta_txt = os.path.join(BASE_DIR, "data/bronze/poblacion_2018/TerriData_Dim2.txt")
separador = "|"

departamento_filtrar = "Santander"

carpeta_salida = os.path.join(BASE_DIR, "data/silver/poblacion")
nombre_salida = "poblacion_santander.parquet"

os.makedirs(carpeta_salida, exist_ok=True)

# ==========================================
# 2. CARGAR ARCHIVO
# ==========================================

print("Cargando archivo TXT...")
poblacion = pd.read_csv(ruta_txt, sep=separador, dtype=str)

# ==========================================
# 3. FILTRAR SANTANDER
# ==========================================
print(f"Filtrando datos del departamento '{departamento_filtrar}'...")

pob_filtrado = poblacion[poblacion["Departamento"] == departamento_filtrar].copy()

# ==========================================
# 4. RENOMBRAR COLUMNAS
# ==========================================
pob_filtrado = pob_filtrado.rename(columns={
    "Código Entidad": "codigo_municipio",
    "Entidad": "municipio",
    "Departamento": "departamento",
    "Año": "anio",
    "Mes": "mes",
    "Dato Numérico": "n_poblacion",
    "Indicador": "edad",
    "Unidad de Medida": "genero"
})

# ==========================================
# 5. LIMPIEZA DE NÚMEROS (VALORES ENTEROS)
# ==========================================
pob_filtrado["n_poblacion"] = (
    pob_filtrado["n_poblacion"]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
        .round()
        .astype(int)
)

# ==========================================
# 6. NORMALIZAR GÉNERO (MASCULINO/FEMENINO)
# ==========================================
pob_filtrado["genero"] = (
    pob_filtrado["genero"]
        .fillna("")
        .str.lower()
        .apply(lambda x: "MASCULINO" if "hombre" in x else
                         "FEMENINO" if "mujer" in x else None)
)

# ==========================================
# 7. ELIMINAR FILAS DE PORCENTAJE
# ==========================================
pob_filtrado = pob_filtrado[
    ~pob_filtrado["edad"].str.contains("Porcentaje", case=False, na=False)
]

# ==========================================
# 8. EXTRAER EDAD MÍNIMA DESDE EL TEXTO
# ==========================================
def extraer_edad_min(texto):
    edades = re.findall(r"\d+", texto)
    return int(edades[0]) if edades else None

pob_filtrado["edad_min"] = pob_filtrado["edad"].apply(extraer_edad_min)

# ==========================================
# 9. CLASIFICAR GRUPOS DE EDAD
# ==========================================
def clasificar_edad(e):
    if e is None:
        return None
    if e <= 11:
        return "MENORES"
    elif 12 <= e <= 17:
        return "ADOLESCENTES"
    return "ADULTOS"

pob_filtrado["grupo_edad"] = pob_filtrado["edad_min"].apply(clasificar_edad)

# ==========================================
# 10. AGREGACIÓN FINAL
# ==========================================
pob_agg = (
    pob_filtrado.groupby(
        ["codigo_municipio", "anio", "genero", "grupo_edad"]
    )["n_poblacion"]
    .sum()
    .reset_index()
)

# ==========================================
# 11. EXPORTAR A PARQUET
# ==========================================
ruta_salida = os.path.join(carpeta_salida, nombre_salida)
pob_agg.to_parquet(ruta_salida, index=False)

print("\nArchivo parquet generado correctamente en:")
print(ruta_salida)
