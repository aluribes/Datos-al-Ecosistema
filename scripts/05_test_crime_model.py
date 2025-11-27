"""
05_test_crime_model.py
======================

Script para probar el modelo de predicción de delitos.

Uso:
    python scripts/05_test_crime_model.py

Este script permite:
    1. Cargar el modelo entrenado
    2. Hacer predicciones de ejemplo
    3. Probar predicciones interactivas por municipio

El mismo código puede ser usado en FastAPI o Streamlit.
"""

from pathlib import Path
import json
from typing import Optional

import joblib
import numpy as np
import pandas as pd

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data" / "gold" / "model"

MODEL_PATH = MODELS_DIR / "crime_rate_model.joblib"
FEATURES_PATH = MODELS_DIR / "crime_rate_model_features.json"
METADATA_PATH = MODELS_DIR / "crime_rate_model_metadata.json"
DATASET_PATH = DATA_DIR / "regression_monthly_dataset.parquet"


class CrimeRatePredictor:
    """
    Predictor de tasa de delitos.
    
    Esta clase encapsula la lógica de predicción y puede ser usada
    directamente en FastAPI, Streamlit, o cualquier otro contexto.
    
    Ejemplo:
        predictor = CrimeRatePredictor()
        predictions = predictor.predict_for_municipio(68001, 2025, 11)
    """
    
    def __init__(self, model_dir: Optional[Path] = None):
        """Carga el modelo y sus metadatos."""
        model_dir = model_dir or MODELS_DIR
        
        self.model = joblib.load(model_dir / "crime_rate_model.joblib")
        
        with open(model_dir / "crime_rate_model_features.json") as f:
            self.feature_names = json.load(f)
        
        with open(model_dir / "crime_rate_model_metadata.json") as f:
            self.metadata = json.load(f)
        
        # Cargar dataset para referencia de municipios
        self._df_reference = pd.read_parquet(DATASET_PATH)
    
    def get_model_info(self) -> dict:
        """Retorna información del modelo."""
        return {
            "target": self.metadata["target"],
            "n_features": self.metadata["n_features"],
            "metrics": self.metadata["metrics"],
            "trained_at": self.metadata["trained_at"],
            "top_features": [f["feature"] for f in self.metadata["top_features"][:5]],
        }
    
    def get_available_municipios(self) -> list[int]:
        """Retorna lista de códigos de municipios disponibles."""
        return sorted(self._df_reference["codigo_municipio"].dropna().unique().tolist())
    
    def get_municipio_history(self, codigo_municipio: int, 
                               last_n_months: int = 12) -> pd.DataFrame:
        """
        Obtiene el historial de un municipio.
        
        Args:
            codigo_municipio: Código DANE del municipio
            last_n_months: Número de meses a retornar
            
        Returns:
            DataFrame con historial del municipio
        """
        df = self._df_reference[
            self._df_reference["codigo_municipio"] == codigo_municipio
        ].copy()
        
        df = df.sort_values("fecha", ascending=False).head(last_n_months)
        
        return df[["codigo_municipio", "anio", "mes", "total_delitos", 
                   "poblacion_total", "lag_1", "roll_mean_3"]].reset_index(drop=True)
    
    def prepare_input(self, row_data: dict) -> pd.DataFrame:
        """
        Prepara input para predicción.
        
        Args:
            row_data: Diccionario con valores de features
            
        Returns:
            DataFrame listo para predicción
        """
        # Crear DataFrame con las features requeridas
        df = pd.DataFrame([row_data])
        
        # Asegurar que todas las features existan
        for feat in self.feature_names:
            if feat not in df.columns:
                df[feat] = np.nan
        
        # Ordenar columnas
        df = df[self.feature_names]
        
        return df
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Realiza predicción.
        
        Args:
            X: DataFrame con features (debe tener las columnas correctas)
            
        Returns:
            Array con predicciones
        """
        # Asegurar orden de columnas
        X = X[self.feature_names]
        return self.model.predict(X)
    
    def predict_for_municipio(self, codigo_municipio: int, 
                               anio: int, mes: int) -> dict:
        """
        Predice delitos para un municipio en un mes específico.
        
        Esta función busca los datos más recientes del municipio y
        construye las features necesarias para la predicción.
        
        Args:
            codigo_municipio: Código DANE del municipio
            anio: Año a predecir
            mes: Mes a predecir (1-12)
            
        Returns:
            Diccionario con predicción e información adicional
        """
        # Obtener datos más recientes del municipio
        df_mun = self._df_reference[
            self._df_reference["codigo_municipio"] == codigo_municipio
        ].sort_values("fecha", ascending=False)
        
        if len(df_mun) == 0:
            return {
                "error": f"Municipio {codigo_municipio} no encontrado",
                "available_municipios": self.get_available_municipios()[:10]
            }
        
        # Usar el registro más reciente como base
        latest = df_mun.iloc[0].copy()
        
        # Actualizar campos temporales
        latest["anio"] = anio
        latest["mes"] = mes
        latest["trimestre"] = (mes - 1) // 3 + 1
        latest["es_fin_ano"] = 1 if mes == 12 else 0
        latest["mes_sin"] = np.sin(2 * np.pi * mes / 12)
        latest["mes_cos"] = np.cos(2 * np.pi * mes / 12)
        
        # Actualizar lags basados en el historial
        if len(df_mun) >= 1:
            latest["lag_1"] = df_mun.iloc[0]["total_delitos"]
        if len(df_mun) >= 3:
            latest["lag_3"] = df_mun.iloc[2]["total_delitos"]
        if len(df_mun) >= 12:
            latest["lag_12"] = df_mun.iloc[11]["total_delitos"]
        
        # Rolling stats
        if len(df_mun) >= 3:
            latest["roll_mean_3"] = df_mun.head(3)["total_delitos"].mean()
            latest["roll_std_3"] = df_mun.head(3)["total_delitos"].std()
        if len(df_mun) >= 12:
            latest["roll_mean_12"] = df_mun.head(12)["total_delitos"].mean()
            latest["roll_std_12"] = df_mun.head(12)["total_delitos"].std()
        
        # Preparar input
        input_data = {feat: latest[feat] for feat in self.feature_names if feat in latest.index}
        X = self.prepare_input(input_data)
        
        # Predecir
        prediction = float(self.predict(X)[0])
        
        # Información adicional
        historical_avg = df_mun["total_delitos"].mean()
        last_month_value = df_mun.iloc[0]["total_delitos"] if len(df_mun) > 0 else None
        
        return {
            "codigo_municipio": codigo_municipio,
            "anio": anio,
            "mes": mes,
            "prediccion_delitos": round(prediction, 1),
            "prediccion_delitos_int": int(round(prediction)),
            "promedio_historico": round(historical_avg, 1),
            "ultimo_mes_real": int(last_month_value) if last_month_value else None,
            "cambio_vs_promedio": round((prediction - historical_avg) / historical_avg * 100, 1),
            "poblacion_total": int(latest["poblacion_total"]),
        }
    
    def predict_batch(self, municipios: list[int], anio: int, mes: int) -> list[dict]:
        """
        Predice para múltiples municipios a la vez.
        
        Args:
            municipios: Lista de códigos de municipio
            anio: Año a predecir
            mes: Mes a predecir
            
        Returns:
            Lista de diccionarios con predicciones
        """
        return [
            self.predict_for_municipio(mun, anio, mes) 
            for mun in municipios
        ]
    
    def predict_all_municipios(self, anio: int, mes: int) -> pd.DataFrame:
        """
        Predice para todos los municipios.
        
        Args:
            anio: Año a predecir
            mes: Mes a predecir
            
        Returns:
            DataFrame con predicciones para todos los municipios
        """
        municipios = self.get_available_municipios()
        results = self.predict_batch(municipios, anio, mes)
        
        # Filtrar errores
        valid_results = [r for r in results if "error" not in r]
        
        return pd.DataFrame(valid_results)


def demo_predictions(predictor: CrimeRatePredictor) -> None:
    """Demuestra predicciones con ejemplos."""
    
    print("\n" + "=" * 60)
    print("📊 DEMO DE PREDICCIONES")
    print("=" * 60)
    
    # Municipios de ejemplo (Bucaramanga y algunos más)
    demo_municipios = [68001, 68307, 68081, 68276]  # Bucaramanga, Girón, Barrancabermeja, Floridablanca
    
    print("\n🔮 Predicciones para Diciembre 2025:")
    print("-" * 60)
    
    for codigo in demo_municipios:
        result = predictor.predict_for_municipio(codigo, 2025, 12)
        
        if "error" in result:
            print(f"  ❌ Municipio {codigo}: {result['error']}")
            continue
        
        print(f"\n  📍 Municipio {codigo}:")
        print(f"     Predicción: {result['prediccion_delitos_int']} delitos")
        print(f"     Promedio histórico: {result['promedio_historico']:.1f}")
        print(f"     Último mes real: {result['ultimo_mes_real']}")
        print(f"     Cambio vs promedio: {result['cambio_vs_promedio']:+.1f}%")
        print(f"     Población: {result['poblacion_total']:,}")


def demo_batch_prediction(predictor: CrimeRatePredictor) -> None:
    """Demuestra predicción batch."""
    
    print("\n" + "=" * 60)
    print("🚀 PREDICCIÓN BATCH (TODOS LOS MUNICIPIOS)")
    print("=" * 60)
    
    import time
    
    start = time.perf_counter()
    df_pred = predictor.predict_all_municipios(2025, 12)
    elapsed = time.perf_counter() - start
    
    print(f"\n  ⏱️ Tiempo total: {elapsed:.2f} segundos")
    print(f"  📊 Municipios predichos: {len(df_pred)}")
    
    # Top 5 con más delitos predichos
    print("\n  🔴 TOP 5 - Mayor cantidad de delitos predichos:")
    top5 = df_pred.nlargest(5, "prediccion_delitos_int")
    for _, row in top5.iterrows():
        print(f"     Municipio {row['codigo_municipio']}: {row['prediccion_delitos_int']} delitos")
    
    # Top 5 con mayor incremento
    print("\n  📈 TOP 5 - Mayor incremento vs promedio histórico:")
    top5_inc = df_pred.nlargest(5, "cambio_vs_promedio")
    for _, row in top5_inc.iterrows():
        print(f"     Municipio {row['codigo_municipio']}: {row['cambio_vs_promedio']:+.1f}%")


def demo_api_usage() -> None:
    """Muestra cómo usar el predictor en una API."""
    
    print("\n" + "=" * 60)
    print("💡 EJEMPLO DE USO EN FASTAPI")
    print("=" * 60)
    
    code_example = '''
# En tu archivo de FastAPI (app/main.py):

from fastapi import FastAPI
from pydantic import BaseModel
from scripts.predict_crime import CrimeRatePredictor

app = FastAPI()
predictor = CrimeRatePredictor()

class PredictionRequest(BaseModel):
    codigo_municipio: int
    anio: int
    mes: int

@app.post("/predict")
def predict(request: PredictionRequest):
    return predictor.predict_for_municipio(
        request.codigo_municipio,
        request.anio,
        request.mes
    )

@app.get("/predict/all/{anio}/{mes}")
def predict_all(anio: int, mes: int):
    df = predictor.predict_all_municipios(anio, mes)
    return df.to_dict("records")
'''
    print(code_example)


def main():
    """Ejecuta las demos."""
    
    print("=" * 70)
    print("🧪 PRUEBA DEL MODELO DE PREDICCIÓN DE DELITOS")
    print("=" * 70)
    
    # Verificar que el modelo existe
    if not MODEL_PATH.exists():
        print(f"\n❌ ERROR: Modelo no encontrado en {MODEL_PATH}")
        print("   Ejecuta primero: python scripts/05_train_crime_rate_model.py")
        return
    
    # Cargar predictor
    print("\nCargando modelo...")
    predictor = CrimeRatePredictor()
    
    # Información del modelo
    info = predictor.get_model_info()
    print(f"\n📋 INFORMACIÓN DEL MODELO:")
    print(f"   Target: {info['target']}")
    print(f"   Features: {info['n_features']}")
    print(f"   R² Score: {info['metrics']['r2']:.4f}")
    print(f"   RMSE: {info['metrics']['rmse']:.4f}")
    print(f"   Top features: {', '.join(info['top_features'])}")
    
    # Demos
    demo_predictions(predictor)
    demo_batch_prediction(predictor)
    demo_api_usage()
    
    print("\n" + "=" * 70)
    print("✅ PRUEBA COMPLETADA")
    print("=" * 70)


if __name__ == "__main__":
    main()
