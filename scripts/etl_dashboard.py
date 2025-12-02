import pandas as pd
import os
import numpy as np

# Definir directorios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DASHBOARD_DIR = os.path.join(BASE_DIR, "data", "gold", "dashboard")
OUTPUT_FILE = os.path.join(DATA_DASHBOARD_DIR, "historico_integrado.parquet")

def build_integrated_df(metas, mandatos, poblacion, policia, municipios, delitos_bucaramanga, delitos_informaticos):
    """
    Lógica original de integración de datos.
    """
    print("   -> Iniciando integración de dataframes...")
    
    # Copias de trabajo
    df_pol = policia.copy()
    df_buc = delitos_bucaramanga.copy()
    df_inf = delitos_informaticos.copy()

    # Normalizaciones
    if "edad" in df_buc.columns and "edad_persona" not in df_buc.columns:
        df_buc = df_buc.rename(columns={"edad": "edad_persona"})

    for df_src in (df_pol, df_buc, df_inf):
        if "cantidad" in df_src.columns:
            df_src["cantidad"] = pd.to_numeric(df_src["cantidad"], errors="coerce").fillna(0)

    if "delito" not in df_inf.columns:
        df_inf["delito"] = "DELITOS INFORMÁTICOS"

    df_pol["origen"] = "POLICIA_SCRAPING"
    df_buc["origen"] = "DELITOS_BUCARAMANGA"
    df_inf["origen"] = "DELITOS_INFORMATICOS"

    # Unificar hechos
    fact = pd.concat([df_pol, df_buc, df_inf], ignore_index=True, sort=False)
    fact.columns = [c.strip() for c in fact.columns]

    # Eliminar redundancias espaciales
    for col in ["departamento", "municipio", "codigo_departamento"]:
        if col in fact.columns:
            fact = fact.drop(columns=col)

    # Join Municipios
    fact = fact.merge(
        municipios[["codigo_municipio", "codigo_departamento", "departamento", "municipio"]],
        on="codigo_municipio",
        how="left",
    )

    # Join Población
    fact = fact.merge(
        poblacion[["codigo_municipio", "anio", "n_poblacion"]],
        on=["codigo_municipio", "anio"],
        how="left",
    )

    # Join Mandatos y Metas
    fact = fact.merge(mandatos, on="anio", how="left")
    fact = fact.merge(metas, on="mandato", how="left")

    # Tipos de datos
    fact["anio"] = pd.to_numeric(fact["anio"], errors="coerce").astype("Int64")
    fact["mes"] = pd.to_numeric(fact["mes"], errors="coerce").astype("Int64")
    
    # Manejo seguro de días (a veces vienen nulos o con ruido)
    fact["dia"] = pd.to_numeric(fact["dia"], errors="coerce").fillna(1).astype("Int64")

    fact["delito"] = fact["delito"].astype(str).str.upper()
    fact["municipio"] = fact["municipio"].astype(str).str.upper()

    # Cálculo de tasa pre-procesado
    fact["tasa_100k"] = np.where(
        fact["n_poblacion"] > 0,
        fact["cantidad"] / fact["n_poblacion"] * 1e5,
        np.nan,
    )
    
    return fact

def main():
    print("--- INICIANDO PROCESO ETL ---")
    
    # 1. Cargar fuentes raw
    print("1. Cargando archivos parquet base...")
    metas = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "metas.parquet"))
    mandatos = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "mandatos.parquet"))
    poblacion = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "poblacion_santander.parquet"))
    policia = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "policia_santander.parquet"))
    municipios = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "municipios.parquet"))
    delitos_bucaramanga = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "delitos_bucaramanga.parquet"))
    delitos_informaticos = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "delitos_informaticos.parquet"))

    # Limpieza de columnas inicial
    for df in (metas, mandatos, poblacion, policia, municipios, delitos_bucaramanga, delitos_informaticos):
        df.columns = [c.strip() for c in df.columns]

    # 2. Ejecutar integración
    print("2. Construyendo dataframe integrado...")
    df_final = build_integrated_df(metas, mandatos, poblacion, policia, municipios, delitos_bucaramanga, delitos_informaticos)

    # 3. Guardar resultado optimizado
    print(f"3. Guardando archivo optimizado en: {OUTPUT_FILE}")
    # Usamos compresión snappy para velocidad de lectura posterior
    df_final.to_parquet(OUTPUT_FILE, index=False, compression='snappy')
    
    print("--- PROCESO TERMINADO CON ÉXITO ---")

if __name__ == "__main__":
    main()