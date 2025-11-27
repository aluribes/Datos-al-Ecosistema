# Fase 5: Entrenamiento de Modelos

Este documento describe el proceso de entrenamiento del modelo de predicción de delitos.

---

## Resumen

| Script | Entrada | Salida | Propósito |
|--------|---------|--------|-----------|
| `05_train_crime_rate_model.py` | `regression_monthly_dataset.parquet` | `models/crime_rate_model.joblib` | Entrenar modelo LightGBM |
| `05_test_crime_model.py` | `crime_rate_model.joblib` | Predicciones en consola | Probar y validar modelo |

---

## 🎯 Modelo: Predicción de Delitos por Municipio

### Objetivo

Predecir `total_delitos` (número total de delitos) para un municipio en un mes específico.

### ¿Por qué LightGBM?

| Característica | Beneficio |
|----------------|-----------|
| **Velocidad de inferencia** | ~0.014 ms por predicción (ideal para APIs) |
| **Manejo de NaN** | No requiere imputación manual |
| **Entrenamiento rápido** | ~500 iteraciones en segundos |
| **Buen rendimiento** | R² > 0.93 sin tuning extensivo |

---

## 📊 Métricas del Modelo

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **R²** | 0.9314 | 93% de varianza explicada |
| **RMSE** | 29.58 | Error cuadrático medio |
| **MAE** | 5.54 | Error absoluto promedio ~5.5 delitos |
| **MAPE** | 8.02% | Error porcentual promedio |

### Velocidad de Inferencia

| Operación | Tiempo |
|-----------|--------|
| Predicción única | ~1.1 ms |
| Batch 100 predicciones | ~1.4 ms |
| Todos los municipios (87) | ~0.6 segundos |

---

## 🔧 Proceso de Entrenamiento

### 1. Preparación de Features

```
Dataset: regression_monthly_dataset.parquet (9,143 filas × 60 columnas)
         ↓
Excluir: identificadores, targets, fechas
         ↓
Features finales: 40 columnas numéricas
```

**Features utilizadas:**

| Categoría | Features |
|-----------|----------|
| **Geográficas** | `area`, `area_km2`, `n_centros_poblados`, `densidad_poblacional` |
| **Demográficas** | `poblacion_total`, `poblacion_*`, `proporcion_*` |
| **Temporales** | `anio`, `mes`, `trimestre`, `es_fin_ano`, `mes_sin`, `mes_cos` |
| **Calendario** | `n_dias_semana`, `n_fines_de_semana`, `n_festivos`, `n_dias_laborales` |
| **Lags** | `lag_1`, `lag_3`, `lag_12` |
| **Rolling stats** | `roll_mean_3`, `roll_mean_12`, `roll_std_3`, `roll_std_12` |
| **Variaciones** | `pct_change_1`, `pct_change_3`, `pct_change_12` |

### 2. División de Datos (Temporal)

```
Datos históricos (< Nov 2024)  →  Train + Validation
Últimos 12 meses (≥ Nov 2024)  →  Test

Train: 7,078 registros
Validation: 1,250 registros (early stopping)
Test: 815 registros
```

### 3. Entrenamiento

- **Early stopping**: Detiene cuando validation RMSE no mejora en 50 iteraciones
- **Mejor iteración**: ~456 (de 500 máximo)

### 4. Top 10 Features Más Importantes

| # | Feature | Importancia |
|---|---------|-------------|
| 1 | `n_dias_semana` | 1286 |
| 2 | `roll_std_3` | 1195 |
| 3 | `roll_mean_3` | 1123 |
| 4 | `n_fines_de_semana` | 1103 |
| 5 | `lag_1` | 952 |
| 6 | `pct_change_1` | 917 |
| 7 | `n_dias_laborales` | 844 |
| 8 | `lag_3` | 806 |
| 9 | `pct_change_3` | 690 |
| 10 | `lag_12` | 643 |

> 💡 Las features temporales y de tendencia (lags, rolling) son las más predictivas.

---

## 📁 Archivos Generados

```
models/
├── crime_rate_model.joblib           # Modelo serializado
├── crime_rate_model_features.json    # Lista de 40 features
├── crime_rate_model_metadata.json    # Métricas, config, top features
└── crime_rate_model_importance.csv   # Importancia de todas las features
```

---

## 🧪 Prueba del Modelo

### Uso Básico

```bash
python scripts/05_test_crime_model.py
```

### Clase `CrimeRatePredictor`

```python
from scripts.predict_crime import CrimeRatePredictor

predictor = CrimeRatePredictor()

# Predicción para un municipio
result = predictor.predict_for_municipio(68001, 2025, 12)
# {
#     "codigo_municipio": 68001,
#     "prediccion_delitos": 877,
#     "promedio_historico": 319.7,
#     "cambio_vs_promedio": +174.3%,
#     ...
# }

# Predicción para todos los municipios
df = predictor.predict_all_municipios(2025, 12)
```

### Métodos Disponibles

| Método | Descripción |
|--------|-------------|
| `predict_for_municipio(codigo, anio, mes)` | Predicción individual |
| `predict_batch(municipios, anio, mes)` | Lista de predicciones |
| `predict_all_municipios(anio, mes)` | DataFrame con todos |
| `get_available_municipios()` | Lista de códigos válidos |
| `get_municipio_history(codigo, n)` | Historial de un municipio |
| `get_model_info()` | Métricas y metadatos |

---

## 🚀 Uso en Producción

### FastAPI

```python
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
```

### Streamlit Dashboard

```python
import streamlit as st
from scripts.predict_crime import CrimeRatePredictor

predictor = CrimeRatePredictor()

municipio = st.selectbox("Municipio", predictor.get_available_municipios())
mes = st.slider("Mes", 1, 12)

if st.button("Predecir"):
    result = predictor.predict_for_municipio(municipio, 2025, mes)
    st.metric("Predicción", f"{result['prediccion_delitos_int']} delitos")
```

---

## 📋 Ejecución Completa

```bash
# 1. Entrenar modelo
python scripts/05_train_crime_rate_model.py

# 2. Probar modelo
python scripts/05_test_crime_model.py
```

---

## ❓ Preguntas Frecuentes

### ¿Por qué la predicción es diferente al último mes real?

El modelo predice basándose en tendencias históricas, estacionalidad y patrones. Si hay un cambio abrupto reciente, el modelo lo incorporará gradualmente a través de los lags.

### ¿Puedo predecir más de un mes adelante?

Actualmente el modelo predice el siguiente mes. Para horizontes más largos, se necesitaría:
1. Predicciones iterativas (predecir mes 1, usar como lag para mes 2, etc.)
2. O un modelo específico para series temporales (Prophet, LSTM)

### ¿Cómo actualizo el modelo con nuevos datos?

1. Actualizar `regression_monthly_dataset.parquet` con nuevos datos
2. Re-ejecutar `05_train_crime_rate_model.py`
3. El modelo anterior se sobrescribe automáticamente
