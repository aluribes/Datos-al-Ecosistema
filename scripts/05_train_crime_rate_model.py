"""
05_train_crime_rate_model.py
============================

Entrena un modelo LightGBM para predecir la tasa de delitos por municipio.

Entrada:
    data/gold/model/regression_monthly_dataset.parquet

Salida:
    models/crime_rate_model.joblib          - Modelo serializado
    models/crime_rate_model_metadata.json   - Metadatos del modelo
    models/crime_rate_model_features.json   - Lista de features usadas

Target principal:
    - total_delitos: Total de delitos en el municipio-mes

¿Por qué LightGBM?
    - Entrenamiento rápido
    - Predicciones extremadamente rápidas (ideal para APIs)
    - Maneja bien datos faltantes
    - Buen rendimiento sin mucho tuning

Uso:
    python scripts/05_train_crime_rate_model.py

El modelo generado puede ser cargado para predicciones:
    import joblib
    model = joblib.load('models/crime_rate_model.joblib')
    predictions = model.predict(X_new)
"""

from pathlib import Path
import json
import warnings
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import lightgbm as lgb

warnings.filterwarnings("ignore")

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "gold" / "model"
MODELS_DIR = BASE_DIR / "models"

INPUT_FILE = DATA_DIR / "regression_monthly_dataset.parquet"

# Target a predecir
TARGET = "total_delitos"

# Columnas a excluir como features (identificadores, targets, fechas)
EXCLUDE_COLS = [
    # Identificadores
    "codigo_departamento",
    "codigo_municipio", 
    # Target y columnas derivadas directamente del target
    "total_delitos",
    # Tipos de delito individuales (podemos usarlos como targets alternativos)
    "ABIGEATO", "AMENAZAS", "DELITOS SEXUALES", "EXTORSION",
    "HOMICIDIOS", "HURTOS", "LESIONES", "VIOLENCIA INTRAFAMILIAR",
    # Tasas (derivadas del target)
    "tasa_abigeato", "tasa_amenazas", "tasa_delitos sexuales", "tasa_extorsion",
    "tasa_homicidios", "tasa_hurtos", "tasa_lesiones", "tasa_violencia intrafamiliar",
    # Fechas
    "fecha",
]

# Parámetros de LightGBM optimizados para velocidad y buen rendimiento
LGBM_PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "boosting_type": "gbdt",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "max_depth": -1,  # Sin límite
    "min_child_samples": 20,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "n_estimators": 500,
    "early_stopping_rounds": 50,
    "verbose": -1,
    "random_state": 42,
    "n_jobs": -1,  # Usar todos los cores
}


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def load_data() -> pd.DataFrame:
    """Carga el dataset de regresión mensual."""
    print("Cargando dataset...")
    df = pd.read_parquet(INPUT_FILE)
    print(f"  - Registros: {len(df):,}")
    print(f"  - Columnas: {len(df.columns)}")
    return df


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """
    Prepara features y target para entrenamiento.
    
    Returns:
        X: DataFrame con features
        y: Series con target
        feature_names: Lista de nombres de features
    """
    print("\nPreparando features...")
    
    # Seleccionar columnas que no están en EXCLUDE_COLS
    feature_cols = [c for c in df.columns if c not in EXCLUDE_COLS]
    
    X = df[feature_cols].copy()
    y = df[TARGET].copy()
    
    # Convertir tipos para LightGBM
    for col in X.columns:
        if X[col].dtype == "Int64":
            X[col] = X[col].astype(float)
        elif X[col].dtype == "Float64":
            X[col] = X[col].astype(float)
    
    print(f"  - Features seleccionadas: {len(feature_cols)}")
    print(f"  - Target: {TARGET}")
    print(f"  - Features: {feature_cols}")
    
    return X, y, feature_cols


def temporal_train_test_split(
    X: pd.DataFrame, 
    y: pd.Series, 
    df_original: pd.DataFrame,
    test_months: int = 12
) -> tuple:
    """
    Split temporal: entrena con datos históricos, testea con los últimos N meses.
    
    Esto simula el uso real: predecir el futuro basándose en el pasado.
    """
    print(f"\nDivisión temporal (últimos {test_months} meses para test)...")
    
    # Ordenar por fecha
    df_temp = df_original[["fecha"]].copy()
    df_temp["idx"] = range(len(df_temp))
    df_temp = df_temp.sort_values("fecha")
    
    # Encontrar fecha de corte
    unique_dates = df_temp["fecha"].dropna().unique()
    unique_dates = sorted(unique_dates)
    
    if len(unique_dates) < test_months + 1:
        # Si no hay suficientes meses, usar split simple
        print("  ⚠ Pocos meses únicos, usando split aleatorio 80/20")
        return train_test_split(X, y, test_size=0.2, random_state=42)
    
    cutoff_date = unique_dates[-test_months]
    
    # Crear máscaras
    train_mask = df_original["fecha"] < cutoff_date
    test_mask = df_original["fecha"] >= cutoff_date
    
    X_train = X[train_mask]
    X_test = X[test_mask]
    y_train = y[train_mask]
    y_test = y[test_mask]
    
    print(f"  - Fecha de corte: {cutoff_date}")
    print(f"  - Train: {len(X_train):,} registros")
    print(f"  - Test: {len(X_test):,} registros (últimos {test_months} meses)")
    
    return X_train, X_test, y_train, y_test


def train_model(X_train: pd.DataFrame, y_train: pd.Series, 
                X_val: pd.DataFrame, y_val: pd.Series) -> lgb.LGBMRegressor:
    """
    Entrena modelo LightGBM con early stopping.
    """
    print("\nEntrenando modelo LightGBM...")
    
    model = lgb.LGBMRegressor(**LGBM_PARAMS)
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
    )
    
    print(f"  - Mejor iteración: {model.best_iteration_}")
    print(f"  - Mejor score (RMSE): {model.best_score_['valid_0']['rmse']:.4f}")
    
    return model


def evaluate_model(model: lgb.LGBMRegressor, X_test: pd.DataFrame, 
                   y_test: pd.Series) -> dict:
    """
    Evalúa el modelo con múltiples métricas.
    """
    print("\nEvaluando modelo...")
    
    y_pred = model.predict(X_test)
    
    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "r2": float(r2_score(y_test, y_pred)),
        "mape": float(np.mean(np.abs((y_test - y_pred) / np.maximum(y_test, 1))) * 100),
    }
    
    print(f"\n  📊 MÉTRICAS DE EVALUACIÓN:")
    print(f"     RMSE:  {metrics['rmse']:.4f} (error cuadrático medio)")
    print(f"     MAE:   {metrics['mae']:.4f} (error absoluto medio)")
    print(f"     R²:    {metrics['r2']:.4f} (varianza explicada)")
    print(f"     MAPE:  {metrics['mape']:.2f}% (error porcentual)")
    
    # Análisis de predicciones
    print(f"\n  📈 ANÁLISIS DE PREDICCIONES:")
    print(f"     Real - min: {y_test.min():.0f}, max: {y_test.max():.0f}, media: {y_test.mean():.2f}")
    print(f"     Pred - min: {y_pred.min():.0f}, max: {y_pred.max():.0f}, media: {y_pred.mean():.2f}")
    
    return metrics


def get_feature_importance(model: lgb.LGBMRegressor, 
                           feature_names: list[str]) -> pd.DataFrame:
    """
    Obtiene importancia de features.
    """
    importance = pd.DataFrame({
        "feature": feature_names,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)
    
    print("\n  🔝 TOP 10 FEATURES MÁS IMPORTANTES:")
    for i, row in importance.head(10).iterrows():
        print(f"     {row['feature']}: {row['importance']}")
    
    return importance


def save_model(model: lgb.LGBMRegressor, feature_names: list[str], 
               metrics: dict, importance: pd.DataFrame) -> None:
    """
    Guarda el modelo y sus metadatos.
    """
    print("\nGuardando modelo...")
    
    ensure_folder(MODELS_DIR)
    
    # 1. Guardar modelo
    model_path = MODELS_DIR / "crime_rate_model.joblib"
    joblib.dump(model, model_path)
    print(f"  ✔ Modelo: {model_path}")
    
    # 2. Guardar features
    features_path = MODELS_DIR / "crime_rate_model_features.json"
    with open(features_path, "w") as f:
        json.dump(feature_names, f, indent=2)
    print(f"  ✔ Features: {features_path}")
    
    # 3. Guardar metadatos
    metadata = {
        "model_type": "LightGBM",
        "target": TARGET,
        "n_features": len(feature_names),
        "metrics": metrics,
        "lgbm_params": LGBM_PARAMS,
        "best_iteration": model.best_iteration_,
        "trained_at": datetime.now().isoformat(),
        "dataset": str(INPUT_FILE),
        "top_features": importance.head(10).to_dict("records"),
    }
    
    metadata_path = MODELS_DIR / "crime_rate_model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"  ✔ Metadatos: {metadata_path}")
    
    # 4. Guardar importancia completa
    importance_path = MODELS_DIR / "crime_rate_model_importance.csv"
    importance.to_csv(importance_path, index=False)
    print(f"  ✔ Importancia features: {importance_path}")


def benchmark_inference_speed(model: lgb.LGBMRegressor, 
                               X_sample: pd.DataFrame) -> dict:
    """
    Mide la velocidad de inferencia del modelo.
    """
    import time
    
    print("\n⚡ BENCHMARK DE VELOCIDAD:")
    
    # Single prediction
    single_row = X_sample.iloc[[0]]
    times_single = []
    for _ in range(100):
        start = time.perf_counter()
        _ = model.predict(single_row)
        times_single.append(time.perf_counter() - start)
    
    avg_single = np.mean(times_single) * 1000  # ms
    print(f"   Predicción única: {avg_single:.3f} ms")
    
    # Batch prediction (100 rows)
    batch_100 = X_sample.head(100)
    times_batch = []
    for _ in range(100):
        start = time.perf_counter()
        _ = model.predict(batch_100)
        times_batch.append(time.perf_counter() - start)
    
    avg_batch = np.mean(times_batch) * 1000  # ms
    print(f"   Batch 100 filas: {avg_batch:.3f} ms ({avg_batch/100:.4f} ms/fila)")
    
    # Full dataset
    start = time.perf_counter()
    _ = model.predict(X_sample)
    full_time = (time.perf_counter() - start) * 1000
    print(f"   Dataset completo ({len(X_sample):,} filas): {full_time:.2f} ms")
    
    return {
        "single_prediction_ms": avg_single,
        "batch_100_ms": avg_batch,
        "full_dataset_ms": full_time,
        "predictions_per_second": len(X_sample) / (full_time / 1000),
    }


def main():
    """Pipeline principal de entrenamiento."""
    print("=" * 70)
    print("🎯 ENTRENAMIENTO DE MODELO: PREDICCIÓN DE DELITOS POR MUNICIPIO")
    print("=" * 70)
    
    # 1. Cargar datos
    df = load_data()
    
    # 2. Preparar features
    X, y, feature_names = prepare_features(df)
    
    # 3. Split temporal
    X_train, X_test, y_train, y_test = temporal_train_test_split(
        X, y, df, test_months=12
    )
    
    # 4. Split train/validation para early stopping
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15, random_state=42
    )
    print(f"  - Train final: {len(X_train):,}")
    print(f"  - Validation: {len(X_val):,}")
    
    # 5. Entrenar modelo
    model = train_model(X_train, y_train, X_val, y_val)
    
    # 6. Evaluar en test set
    metrics = evaluate_model(model, X_test, y_test)
    
    # 7. Importancia de features
    importance = get_feature_importance(model, feature_names)
    
    # 8. Benchmark de velocidad
    speed_metrics = benchmark_inference_speed(model, X)
    metrics["speed"] = speed_metrics
    
    # 9. Guardar modelo
    save_model(model, feature_names, metrics, importance)
    
    print("\n" + "=" * 70)
    print("✅ ENTRENAMIENTO COMPLETADO")
    print("=" * 70)
    print(f"\nPróximos pasos:")
    print(f"  1. Probar el modelo: python scripts/05_test_crime_model.py")
    print(f"  2. El modelo está listo para usar en FastAPI/Dashboard")
    print(f"\nArchivos generados en {MODELS_DIR}/:")
    print(f"  - crime_rate_model.joblib (modelo)")
    print(f"  - crime_rate_model_features.json (features requeridas)")
    print(f"  - crime_rate_model_metadata.json (métricas y config)")


if __name__ == "__main__":
    main()
