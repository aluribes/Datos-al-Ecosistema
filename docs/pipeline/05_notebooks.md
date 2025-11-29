# Notebooks — Análisis y Modelado

Los notebooks de la sección 05 contienen el análisis exploratorio (EDA), entrenamiento de modelos y generación de artefactos para predicción.

## Estructura de Notebooks

| Notebook | Tipo | Descripción |
|----------|------|-------------|
| `05_regression_monthly_descript.ipynb` | Descriptivo | EDA de regresión mensual |
| `05_regression_monthly_predict.ipynb` | Predictivo | Modelo de regresión mensual |
| `05_regression_annual_descript.ipynb` | Descriptivo | EDA de regresión anual |
| `05_regression_annual_predict.ipynb` | Predictivo | Modelo de regresión anual |
| `05_eda_regression_timeseries.ipynb` | Predictivo | Forecast con Prophet (series temporales) |
| `05_classification_monthly_descript.ipynb` | Descriptivo | EDA de clasificación mensual |
| `05_classification_monthly_predict.ipynb` | Predictivo | Modelo de clasificación mensual |
| `05_classification_event_descript.ipynb` | Descriptivo | EDA de clasificación por evento |
| `05_classification_event_predict.ipynb` | Predictivo | Modelo de clasificación por evento |
| `05_classification_dominant_descript.ipynb` | Descriptivo | EDA de delito/arma dominante |
| `05_classification_dominant_predict.ipynb` | Predictivo | Modelo de clasificación dominante |
| `05_clustering_geo.ipynb` | Clustering | Segmentación geográfica de municipios |

---

## Notebooks Descriptivos (`*_descript.ipynb`)

Contienen análisis exploratorio de datos (EDA):
- Estadísticas descriptivas
- Visualizaciones de distribuciones
- Análisis de correlaciones
- Detección de patrones y outliers
- Preparación de features

**No generan modelos**, solo contexto para entender los datos.

---

## Notebooks Predictivos (`*_predict.ipynb`)

Contienen el pipeline completo de Machine Learning:
1. Carga de datos desde `data/gold/model/`
2. Preprocesamiento (encoding, scaling)
3. División train/test
4. Entrenamiento de modelos base
5. Optimización de hiperparámetros
6. Evaluación con métricas
7. Guardado de artefactos en `models/`

---

## Detalle por Notebook

### Regresión Mensual

**Dataset:** `regression_monthly_dataset.parquet` (9,143 filas)

| Notebook | Objetivo |
|----------|----------|
| `05_regression_monthly_descript.ipynb` | Explorar patrones mensuales de delitos por municipio |
| `05_regression_monthly_predict.ipynb` | Predecir `total_delitos` por municipio-mes |

**Modelos:** XGBoost, Random Forest, Gradient Boosting  
**Métricas:** MAE, RMSE, R², MAPE

---

### Regresión Anual

**Dataset:** `regression_annual_dataset.parquet` (1,334 filas)

| Notebook | Objetivo |
|----------|----------|
| `05_regression_annual_descript.ipynb` | Análisis espacial y clustering de municipios |
| `05_regression_annual_predict.ipynb` | Predecir delitos anuales por municipio |

**Modelos:** XGBoost, Random Forest, Ridge, Lasso  
**Métricas:** MAE, RMSE, R², MAPE

---

### Series Temporales (Prophet)

**Dataset:** `regression_timeseries_dataset.parquet` (190 filas)

| Notebook | Objetivo |
|----------|----------|
| `05_eda_regression_timeseries.ipynb` | Forecast de delitos a nivel departamental |

**Contenido:**
- Descomposición de serie (tendencia, estacionalidad, residuos)
- Test de estacionariedad (Dickey-Fuller)
- Modelado con Prophet
- Optimización de hiperparámetros
- Forecast a 12 meses

**Modelo:** Prophet  
**Métricas:** MAE, RMSE, R², MAPE

---

### Clasificación Mensual

**Dataset:** `classification_monthly_dataset.parquet` (9,143 filas)

| Notebook | Objetivo |
|----------|----------|
| `05_classification_monthly_descript.ipynb` | Explorar distribución de niveles de riesgo |
| `05_classification_monthly_predict.ipynb` | Clasificar `nivel_riesgo` (BAJO/MEDIO/ALTO) e `incremento_delitos` |

**Modelos:** XGBoost, Random Forest, Logistic Regression  
**Métricas:** Accuracy, F1-Score, ROC-AUC, Confusion Matrix

---

### Clasificación por Evento

**Dataset:** `classification_event_dataset.parquet` (279,762 filas)

| Notebook | Objetivo |
|----------|----------|
| `05_classification_event_descript.ipynb` | Explorar perfiles de eventos delictivos |
| `05_classification_event_predict.ipynb` | Clasificar `delito`, `armas_medios`, `perfil` |

**Modelos:** MultiOutputClassifier(XGBoost), Random Forest  
**Técnicas:** SMOTE para balance de clases  
**Métricas:** Accuracy, F1-Score por target

---

### Clasificación Dominante

**Dataset:** `classification_dominant_dataset.parquet` (33,408 filas)

| Notebook | Objetivo |
|----------|----------|
| `05_classification_dominant_descript.ipynb` | Explorar delitos y armas dominantes |
| `05_classification_dominant_predict.ipynb` | Predecir `delito_dominante` y `arma_dominante` |

**Modelos:** MultiOutputClassifier(XGBoost), Random Forest  
**Métricas:** Accuracy, F1-Score, Confusion Matrix

---

### Clustering Geográfico

**Dataset:** `clustering_geo_dataset.parquet` (9,143 filas)

| Notebook | Objetivo |
|----------|----------|
| `05_clustering_geo.ipynb` | Segmentar municipios por perfil delictivo |

**Contenido:**
- Análisis de features para clustering
- Determinación de número óptimo de clusters (Elbow, Silhouette)
- KMeans con 4 clusters
- Caracterización de cada cluster
- Guardado de modelo y asignaciones

**Modelo:** KMeans (n_clusters=4)  
**Clusters:**
| Cluster | Descripción |
|---------|-------------|
| 0 | Municipios pequeños, baja criminalidad |
| 1 | Ciudades grandes, alta criminalidad |
| 2 | Ciudades medianas |
| 3 | Área metropolitana Bucaramanga |

---

## Artefactos Generados

Los notebooks predictivos guardan artefactos en `models/`:

```
models/
├── clustering/
│   └── geo_municipal/
│       ├── kmeans_model.joblib
│       └── metadata.json
├── descriptivo/
│   ├── classification_dominant/
│   ├── classification_event/
│   ├── classification_monthly/
│   └── clustering_geo/
├── predictivos/
│   ├── classification_dominant/
│   ├── classification_event/
│   └── classification_monthly/
└── timeserie/
    └── regression_timeseries/
        ├── prophet_model.joblib
        ├── forecast_futuro.csv
        └── metadata.json
```

Cada carpeta de modelo contiene:
- `*.joblib` — Modelo serializado
- `metadata.json` — Hiperparámetros, métricas, fechas
- `*.csv` — Predicciones o datos auxiliares (opcional)

---

## Ejecución

Los notebooks requieren que los datasets de `data/gold/model/` existan. Ejecutar primero la Sección 04:

```bash
python scripts/04_generate_analytics.py
python scripts/04_generate_regression_monthly_dataset.py
# ... etc
```

Luego abrir los notebooks en Jupyter o VS Code.

---

## Librerías Principales

| Librería | Uso |
|----------|-----|
| `pandas`, `numpy` | Manipulación de datos |
| `matplotlib`, `seaborn` | Visualización |
| `scikit-learn` | Modelos ML, métricas, preprocessing |
| `xgboost` | Gradient Boosting |
| `prophet` | Series temporales |
| `imbalanced-learn` | SMOTE para balance |
| `joblib` | Serialización de modelos |
