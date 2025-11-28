"""
02_process_silver.py
====================

Procesa y unifica los datos Bronze de Socrata en un esquema Silver estandarizado.

Entrada:
    data/bronze/socrata_api/*.json (7 archivos de delitos)

Salida:
    data/silver/delitos/consolidado_delitos.parquet

Esquema Silver (columnas normalizadas):
    - tipo_delito: str (nombre del delito basado en archivo origen)
    - fecha_hecho: datetime
    - cod_muni: str (5 dígitos, código DANE municipio)
    - municipio: str (mayúsculas)
    - departamento: str (siempre "SANTANDER")
    - genero: str (o "NO REPORTADO" si no existe)
    - arma_medio: str (o "NO REPORTADO" si no existe)
    - cantidad: int
"""

from pathlib import Path
from typing import List

import pandas as pd

# === CONFIGURACIÓN ===
BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze" / "socrata_api"
SILVER_DIR = BASE_DIR / "data" / "silver" / "delitos"

# Mapeo de nombre de archivo a tipo de delito
DELITO_MAP = {
    "homicidios": "HOMICIDIOS",
    "extorsion": "EXTORSION",
    "hurto_personas": "HURTO_PERSONAS",
    "lesiones": "LESIONES",
    "amenazas": "AMENAZAS",
    "delitos_sexuales": "DELITOS_SEXUALES",
    "violencia_intrafamiliar": "VIOLENCIA_INTRAFAMILIAR",
}

# Columnas finales del esquema Silver
SILVER_COLUMNS = [
    "tipo_delito",
    "fecha_hecho",
    "cod_muni",
    "municipio",
    "departamento",
    "genero",
    "arma_medio",
    "cantidad",
]


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
    # Intentar parsear con formato mixto
    return pd.to_datetime(df[date_col], format="mixed", dayfirst=True, errors="coerce")


def get_column_value(df: pd.DataFrame, possible_names: List[str], default: str = "NO REPORTADO") -> pd.Series:
    """
    Busca una columna por varios nombres posibles.
    Si no existe ninguna, retorna una Serie con el valor por defecto.
    """
    for name in possible_names:
        if name in df.columns:
            return df[name].fillna(default).astype(str).str.upper()
    
    return pd.Series([default] * len(df), index=df.index)


def process_file(filepath: Path) -> pd.DataFrame:
    """
    Procesa un archivo JSON Bronze y lo transforma al esquema Silver.
    """
    # Obtener nombre del delito desde el nombre del archivo
    file_stem = filepath.stem
    tipo_delito = DELITO_MAP.get(file_stem, file_stem.upper())
    
    print(f"  Procesando: {filepath.name} -> {tipo_delito}")
    
    # Leer JSON
    df = pd.read_json(filepath)
    
    if df.empty:
        print(f"    ⚠ Archivo vacío")
        return pd.DataFrame(columns=SILVER_COLUMNS)
    
    print(f"    Registros raw: {len(df):,}")
    
    # === TRANSFORMACIONES ===
    
    # Crear DataFrame Silver con el número correcto de filas
    n_rows = len(df)
    
    # 1. tipo_delito (nuevo, basado en nombre de archivo)
    df_silver = pd.DataFrame()
    df_silver["tipo_delito"] = [tipo_delito] * n_rows
    
    # 2. fecha_hecho (normalizar formatos)
    date_col = "fecha_hecho" if "fecha_hecho" in df.columns else None
    if date_col:
        df_silver["fecha_hecho"] = normalize_date(df, date_col)
    else:
        df_silver["fecha_hecho"] = pd.NaT
    
    # 3. cod_muni (normalizar a 5 dígitos)
    cod_col = None
    for possible in ["cod_muni", "codigo_dane"]:
        if possible in df.columns:
            cod_col = possible
            break
    
    if cod_col:
        df_silver["cod_muni"] = df[cod_col].apply(normalize_cod_muni)
    else:
        df_silver["cod_muni"] = "00000"
    
    # 4. municipio (mayúsculas)
    if "municipio" in df.columns:
        df_silver["municipio"] = df["municipio"].fillna("NO REPORTADO").astype(str).str.upper()
    else:
        df_silver["municipio"] = "NO REPORTADO"
    
    # 5. departamento (siempre SANTANDER)
    df_silver["departamento"] = "SANTANDER"
    
    # 6. genero (unificar columnas genero/sexo)
    df_silver["genero"] = get_column_value(df, ["genero", "sexo"], "NO REPORTADO")
    
    # 7. arma_medio (unificar columna armas_medios)
    df_silver["arma_medio"] = get_column_value(df, ["armas_medios", "arma_medio"], "NO REPORTADO")
    
    # 8. cantidad (entero)
    if "cantidad" in df.columns:
        df_silver["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(1).astype(int)
    else:
        df_silver["cantidad"] = 1
    
    # Asegurar orden de columnas
    df_silver = df_silver[SILVER_COLUMNS]
    
    print(f"    Registros Silver: {len(df_silver):,}")
    
    return df_silver


def main() -> None:
    """Ejecuta el procesamiento Silver."""
    print("=" * 60)
    print("🥈 PROCESAMIENTO SILVER - CONSOLIDACIÓN DE DELITOS")
    print("=" * 60)
    
    # Crear directorio de salida
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    
    # Procesar cada archivo JSON
    dataframes = []
    
    for filepath in sorted(BRONZE_DIR.glob("*.json")):
        try:
            df = process_file(filepath)
            if not df.empty:
                dataframes.append(df)
        except Exception as e:
            print(f"  ✗ Error procesando {filepath.name}: {e}")
    
    if not dataframes:
        print("\n⚠ No se procesaron archivos")
        return
    
    # Concatenar todos los DataFrames
    print("\n" + "-" * 60)
    print("📦 Consolidando datos...")
    
    df_consolidated = pd.concat(dataframes, ignore_index=True)
    
    print(f"  Total registros consolidados: {len(df_consolidated):,}")
    
    # Estadísticas por tipo de delito
    print("\n📊 Registros por tipo de delito:")
    for delito in sorted(df_consolidated["tipo_delito"].unique()):
        count = len(df_consolidated[df_consolidated["tipo_delito"] == delito])
        print(f"    {delito:30} {count:>10,}")
    
    # Estadísticas por año
    df_consolidated["anio"] = df_consolidated["fecha_hecho"].dt.year
    print("\n📊 Registros por año:")
    year_counts = df_consolidated.groupby("anio").size().sort_index()
    for year, count in year_counts.items():
        if pd.notna(year):
            print(f"    {int(year):>6} {count:>10,}")
    
    # Eliminar columna temporal de año
    df_consolidated = df_consolidated.drop(columns=["anio"])
    
    # Guardar en Parquet
    output_path = SILVER_DIR / "consolidado_delitos.parquet"
    df_consolidated.to_parquet(output_path, index=False)
    
    print("\n" + "=" * 60)
    print(f"✅ Guardado en: {output_path}")
    print(f"   Registros: {len(df_consolidated):,}")
    print(f"   Columnas: {df_consolidated.columns.tolist()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
