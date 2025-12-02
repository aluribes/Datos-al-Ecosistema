import pandas as pd
import os
import numpy as np

# Definir directorios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DASHBOARD_DIR = os.path.join(BASE_DIR, "data", "gold", "dashboard")
OUTPUT_FILE = os.path.join(DATA_DASHBOARD_DIR, "historico_integrado.parquet")

def optimize_dtypes(df):
    """
    Reduce el uso de memoria convirtiendo objetos a categorías y
    reduciendo el tamaño de los números (int64 -> int32/16, float64 -> float32).
    """
    print("   -> Optimizando tipos de datos para reducir RAM...")
    
    # 1. Convertir columnas de texto repetitivo a 'category'
    # Esto es lo que MÁS memoria ahorra (puede bajar de 1GB a 100MB)
    for col in df.select_dtypes(include=['object']).columns:
        num_unique_values = len(df[col].unique())
        num_total_values = len(df[col])
        # Si menos del 50% de los valores son únicos, vale la pena convertir a categoría
        if num_unique_values / num_total_values < 0.5:
            df[col] = df[col].astype('category')
            print(f"      Columna '{col}' convertida a category.")

    # 2. Reducir tamaño de números (Downcasting)
    # Pandas usa int64/float64 por defecto. A veces int16 o float32 es suficiente.
    for col in df.select_dtypes(include=['int', 'float']).columns:
        # Ignorar columnas como 'anio' si quieres mantenerlas como int estándar, 
        # pero para conteos y tasas, downcast ayuda.
        try:
            if "int" in str(df[col].dtype):
                df[col] = pd.to_numeric(df[col], downcast='integer')
            else:
                df[col] = pd.to_numeric(df[col], downcast='float')
        except:
            pass
            
    return df

def build_integrated_df(metas, mandatos, poblacion, policia, municipios, delitos_informaticos):
    print("   -> Iniciando integración de dataframes...")
    
    # Copias de trabajo
    df_pol = policia.copy()
    df_inf = delitos_informaticos.copy()

    # Asegurar cantidad numérica
    for df_src in (df_pol, df_inf):
        if "cantidad" in df_src.columns:
            df_src["cantidad"] = pd.to_numeric(df_src["cantidad"], errors="coerce").fillna(0)

    if "delito" not in df_inf.columns:
        df_inf["delito"] = "DELITOS INFORMÁTICOS"

    df_pol["origen"] = "POLICIA_SCRAPING"
    df_inf["origen"] = "DELITOS_INFORMATICOS"

    # Unificar hechos
    fact = pd.concat([df_pol, df_inf], ignore_index=True, sort=False)
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

    # Tipos de datos básicos
    fact["anio"] = pd.to_numeric(fact["anio"], errors="coerce").astype("Int64")
    fact["mes"] = pd.to_numeric(fact["mes"], errors="coerce").astype("Int64")
    fact["dia"] = pd.to_numeric(fact["dia"], errors="coerce").fillna(1).astype("Int64")

    fact["delito"] = fact["delito"].astype(str).str.upper()
    fact["municipio"] = fact["municipio"].astype(str).str.upper()

    # Cálculo de tasa
    fact["tasa_100k"] = np.where(
        fact["n_poblacion"] > 0,
        fact["cantidad"] / fact["n_poblacion"] * 1e5,
        np.nan,
    )
    
    # --- APLICAR OPTIMIZACIÓN DE MEMORIA AQUÍ ---
    fact = optimize_dtypes(fact)
    
    return fact

def main():
    print("--- INICIANDO PROCESO ETL ---")
    
    print("1. Cargando archivos parquet base...")
    metas = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "metas.parquet"))
    mandatos = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "mandatos.parquet"))
    poblacion = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "poblacion_santander.parquet"))
    policia = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "policia_santander.parquet"))
    municipios = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "municipios.parquet"))
    delitos_informaticos = pd.read_parquet(os.path.join(DATA_DASHBOARD_DIR, "delitos_informaticos.parquet"))

    for df in (metas, mandatos, poblacion, policia, municipios, delitos_informaticos):
        df.columns = [c.strip() for c in df.columns]

    print("2. Construyendo dataframe integrado...")
    df_final = build_integrated_df(metas, mandatos, poblacion, policia, municipios, delitos_informaticos)

    print(f"3. Guardando archivo optimizado en: {OUTPUT_FILE}")
    
    # Opción A: Parquet (Equilibrio perfecto)
    # compression='zstd' suele dar mejor compresión que snappy manteniendo buena velocidad
    df_final.to_parquet(OUTPUT_FILE, index=False, compression='zstd')
    
    # Opción B (SOLO SI AÚN ES LENTO): Feather
    # Feather lee más rápido, pero no comprime tanto en disco.
    # df_final.to_feather(OUTPUT_FILE.replace('.parquet', '.feather'))
    
    print("--- PROCESO TERMINADO CON ÉXITO ---")
    print("Nota: Ahora tu app cargará mucho más rápido y consumirá menos RAM.")

if __name__ == "__main__":
    main()