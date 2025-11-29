# Capa Model Data — Preparación para Machine Learning

La capa Model Data contiene los datasets optimizados para entrenamiento de modelos de Machine Learning y visualización en dashboard. Se generan a partir de `gold_integrado.parquet`, `gold_analytics.parquet` y `policia_gold.parquet`.

## Scripts de la Sección 04

| # | Script | Descripción | Entrada | Salida |
|---|--------|-------------|---------|--------|
| 1 | `04_generate_analytics.py` | Enriquece gold_integrado con tasas, lags, rolling | `gold_integrado.parquet` | `gold_analytics.parquet` |
| 2 | `04_generate_dashboard_data.py` | Prepara datos para visualización en dashboard | Silver diversos | `data/gold/dashboard/*.parquet` |
| 3 | `04_generate_regression_monthly_dataset.py` | Dataset regresión mensual | `gold_analytics.parquet` | `regression_monthly_dataset.parquet` |
| 4 | `04_generate_regression_annual_dataset.py` | Dataset regresión anual | `gold_integrado.parquet` | `regression_annual_dataset.parquet` |
| 5 | `04_generate_regression_timeseries_dataset.py` | Serie temporal global | `gold_analytics.parquet` | `regression_timeseries_dataset.parquet` |
| 6 | `04_generate_classification_monthly_dataset.py` | Clasificación riesgo/incremento | `gold_analytics.parquet` | `classification_monthly_dataset.parquet` |
| 7 | `04_generate_classification_event_dataset.py` | Clasificación por evento | `policia_gold.parquet` + `gold_integrado.parquet` | `classification_event_dataset.parquet` |
| 8 | `04_generate_classification_dominant_dataset.py` | Delito/arma dominante | `policia_gold.parquet` | `classification_dominant_dataset.parquet` |
| 9 | `04_generate_clustering_geo_dataset.py` | Clustering geográfico | `gold_integrado.parquet` | `clustering_geo_dataset.parquet` |

---

## 1. Analytics — Enriquecimiento de Gold Integrado

**Script:** `scripts/04_generate_analytics.py`

Genera el dataset analítico enriquecido con tasas por 100k, lags, rolling means y codificación cíclica.

### Entrada y Salida

| | Archivo |
|---|---------|
| **Entrada** | `data/gold/gold_integrado.parquet` |
| **Salida** | `data/gold/analytics/gold_analytics.parquet` |

### Features generados

| Categoría | Columnas |
|-----------|----------|
| **Tasas por 100k** | `tasa_homicidios`, `tasa_hurtos`, `tasa_lesiones`, `tasa_violencia_intrafamiliar`, `tasa_amenazas`, `tasa_delitos_sexuales`, `tasa_extorsion`, `tasa_abigeato` |
| **Codificación cíclica** | `mes_sin`, `mes_cos` |
| **Lags** | `lag_1`, `lag_3`, `lag_12` |
| **Rolling** | `roll_mean_3`, `roll_mean_12`, `roll_std_3`, `roll_std_12` |
| **Variaciones** | `pct_change_1`, `pct_change_3`, `pct_change_12` |

### Ejecución

```bash
python scripts/04_generate_analytics.py
```

---

## 2. Dashboard Data — Datos para Visualización

**Script:** `scripts/04_generate_dashboard_data.py`

Prepara datasets específicos para el dashboard con columnas temporales enriquecidas.

### Entrada y Salida

| Entrada (Silver) | Salida (Gold/dashboard) |
|------------------|-------------------------|
| `dane_geo/geografia_silver.parquet` | `municipios.parquet` |
| `metas/*.parquet` | `<mismo nombre>.parquet` |
| `poblacion/poblacion_santander.parquet` | `poblacion_santander.parquet` |
| `policia_scraping/policia_santander.parquet` | `policia_santander.parquet` |
| `socrata_api/delitos_informaticos.parquet` | `delitos_informaticos.parquet` |
| `socrata_api/delitos_bucaramanga.parquet` | `delitos_bucaramanga.parquet` |

### Columnas temporales agregadas

Para datasets con columna `fecha`:
- `anio`, `mes`, `dia`
- `es_dia_semana`, `es_fin_de_semana`
- `es_fin_mes`
- `es_festivo`, `nombre_festivo`
- `es_dia_laboral`

### Ejecución

```bash
python scripts/04_generate_dashboard_data.py
```

---

## Resumen de Datasets para Modelos (7 consolidados)

| Dataset | Filas | Nivel | Targets | Script |
|---------|-------|-------|---------|--------|
| `regression_monthly_dataset` | 9,143 | Mensual | `total_delitos`, `tasa_*` (8) | `04_generate_regression_monthly_dataset.py` |
| `regression_annual_dataset` | 1,334 | Anual | `total_delitos`, `tasa_*` (8) | `04_generate_regression_annual_dataset.py` |
| `regression_timeseries_dataset` | 190 | Global | `total_delitos`, `tasa_global` | `04_generate_regression_timeseries_dataset.py` |
| `classification_monthly_dataset` | 9,143 | Mensual | `nivel_riesgo`, `incremento_delitos` | `04_generate_classification_monthly_dataset.py` |
| `classification_event_dataset` | 279,762 | Evento | `delito`, `armas_medios`, `perfil` | `04_generate_classification_event_dataset.py` |
| `classification_dominant_dataset` | 33,408 | Mensual | `delito_dominante`, `arma_dominante` | `04_generate_classification_dominant_dataset.py` |
| `clustering_geo_dataset` | 9,143 | Mensual | `cluster_delictivo` (0-3) | `04_generate_clustering_geo_dataset.py` |

---

## Datasets de Regresión

### 3. Regresión Mensual

**Script:** `scripts/04_generate_regression_monthly_dataset.py`

Dataset principal para predecir delitos a nivel municipio-mes.

#### Entrada y Salida

| | Archivo |
|---|---------|
| **Entrada** | `data/gold/analytics/gold_analytics.parquet` |
| **Salida** | `data/gold/model/regression_monthly_dataset.parquet` |

#### Targets disponibles

- `total_delitos`: Total de delitos en el municipio-mes
- `tasa_homicidios`, `tasa_hurtos`, `tasa_lesiones`, `tasa_violencia_intrafamiliar`, `tasa_amenazas`, `tasa_delitos_sexuales`, `tasa_extorsion`, `tasa_abigeato`

#### Features principales

| Categoría | Columnas |
|-----------|----------|
| **Identificadores** | `codigo_municipio`, `codigo_departamento`, `anio`, `mes`, `trimestre` |
| **Demográficas** | `poblacion_total`, `densidad_poblacional`, `proporcion_menores`, `proporcion_adultos`, `proporcion_adolescentes` |
| **Geográficas** | `area_km2`, `centros_por_km2`, `n_centros_poblados` |
| **Temporales** | `mes_sin`, `mes_cos`, `n_festivos`, `n_dias_laborales`, `n_dias_semana`, `n_fines_de_semana` |
| **Lags** | `lag_1`, `lag_3`, `lag_12` |
| **Rolling** | `roll_mean_3`, `roll_mean_12`, `roll_std_3`, `roll_std_12` |
| **Variaciones** | `pct_change_1`, `pct_change_3`, `pct_change_12` |

#### Ejecución

```bash
python scripts/04_generate_regression_monthly_dataset.py
```

---

### 2. Regresión Anual

**Script:** `scripts/04_generate_regression_annual_dataset.py`

Dataset agregado a nivel anual para análisis espacial y comparativas entre municipios.

#### Entrada y Salida

| | Archivo |
|---|---------|
| **Entrada** | `data/gold/gold_integrado.parquet` |
| **Salida** | `data/gold/model/regression_annual_dataset.parquet` |

#### Uso

- Análisis espacial de patrones delictivos
- Modelos que no requieren granularidad mensual
- Comparativas año a año entre municipios

#### Ejecución

```bash
python scripts/04_generate_regression_annual_dataset.py
```

---

### 3. Regresión Serie Temporal

**Script:** `scripts/04_generate_regression_timeseries_dataset.py`

Serie temporal agregada del departamento completo. Una fila por mes.

#### Entrada y Salida

| | Archivo |
|---|---------|
| **Entrada** | `data/gold/analytics/gold_analytics.parquet` |
| **Salida** | `data/gold/model/regression_timeseries_dataset.parquet` |

#### Columnas

| Tipo | Columnas |
|------|----------|
| **Targets** | `total_delitos`, `tasa_global` |
| **Temporales** | `fecha`, `anio`, `mes`, `mes_sin`, `mes_cos` |
| **Lags** | `lag_1`, `lag_3`, `lag_12` |
| **Rolling** | `roll_mean_3`, `roll_mean_12` |
| **Variaciones** | `pct_change_1`, `pct_change_12` |

#### Uso

- Modelos de series temporales (ARIMA, Prophet, LSTM)
- Predicción de tendencia departamental

#### Ejecución

```bash
python scripts/04_generate_regression_timeseries_dataset.py
```

---

## Datasets de Clasificación

### 4. Clasificación Mensual

**Script:** `scripts/04_generate_classification_monthly_dataset.py`

Dataset para clasificar riesgo e incremento a nivel municipio-mes.

#### Entrada y Salida

| | Archivo |
|---|---------|
| **Entrada** | `data/gold/analytics/gold_analytics.parquet` |
| **Salida** | `data/gold/model/classification_monthly_dataset.parquet` |

#### Targets

| Target | Tipo | Valores | Lógica |
|--------|------|---------|--------|
| `nivel_riesgo` | Multiclase | BAJO, MEDIO, ALTO | Basado en percentiles 33/66 de `total_delitos` |
| `incremento_delitos` | Binaria | 0, 1 | 1 si `pct_change_1 > 0` |

#### Distribución típica

```
nivel_riesgo:
  - BAJO:  ~48% (total_delitos <= P33)
  - MEDIO: ~21% (P33 < total_delitos <= P66)
  - ALTO:  ~31% (total_delitos > P66)

incremento_delitos:
  - 0 (Sin incremento): ~62%
  - 1 (Con incremento): ~38%
```

#### Ejecución

```bash
python scripts/04_generate_classification_monthly_dataset.py
```

---

### 5. Clasificación por Evento

**Script:** `scripts/04_generate_classification_event_dataset.py`

Dataset a nivel de evento individual (cada fila = un delito) enriquecido con contexto municipal.

#### Entrada y Salida

| | Archivo |
|---|---------|
| **Entrada** | `policia_gold.parquet` + `gold_integrado.parquet` |
| **Salida** | `data/gold/model/classification_event_dataset.parquet` |

#### Targets

| Target | Categorías | Descripción |
|--------|------------|-------------|
| `delito` | 8 | HOMICIDIOS, HURTOS, LESIONES, AMENAZAS, etc. |
| `armas_medios` | 47 | Arma blanca, contundente, fuego, etc. |
| `perfil` | 9 | MASCULINO_ADULTOS, FEMENINO_ADOLESCENTES, etc. |

#### Features por evento

| Categoría | Columnas |
|-----------|----------|
| **Evento** | `genero`, `edad_persona`, `es_festivo`, `es_dia_semana`, `es_fin_de_semana` |
| **Contexto municipal** | Todas las columnas de `gold_integrado` (población, densidad, tasas, delitos agregados) |
| **Temporales** | `anio`, `mes`, `dia`, `mes_sin`, `mes_cos` |

#### Ejecución

```bash
python scripts/04_generate_classification_event_dataset.py
```

---

### 6. Clasificación Dominante

**Script:** `scripts/04_generate_classification_dominant_dataset.py`

Identifica el delito y arma más frecuente por municipio-mes.

#### Entrada y Salida

| | Archivo |
|---|---------|
| **Entrada** | `data/gold/base/policia_gold.parquet` |
| **Salida** | `data/gold/model/classification_dominant_dataset.parquet` |

#### Columnas

| Columna | Descripción |
|---------|-------------|
| `codigo_municipio` | Código DANE del municipio |
| `anio`, `mes` | Período temporal |
| `delito_dominante` | Tipo de delito más frecuente |
| `count_delito` | Cantidad de eventos del delito dominante |
| `arma_dominante` | Tipo de arma más usada |
| `count_arma` | Cantidad de eventos del arma dominante |

#### Uso

- Responder: ¿Qué tipo de delito predomina en cada municipio-mes?
- Responder: ¿Qué arma se usa más frecuentemente?

#### Ejecución

```bash
python scripts/04_generate_classification_dominant_dataset.py
```

---

## Dataset de Clustering

### 7. Clustering Geográfico

**Script:** `scripts/04_generate_clustering_geo_dataset.py`

Segmentación de municipios basada en perfil delictivo usando KMeans.

#### Entrada y Salida

| | Archivo |
|---|---------|
| **Entrada** | `data/gold/gold_integrado.parquet` |
| **Salida** | `data/gold/model/clustering_geo_dataset.parquet` |

#### Target

- `cluster_delictivo`: Cluster asignado (0-3)

#### Features para clustering

- `total_delitos`
- `poblacion_total`
- `densidad_poblacional`

#### Distribución típica de clusters

| Cluster | % Registros | Delitos promedio | Población promedio | Descripción |
|---------|-------------|-----------------|-------------------|-------------|
| 0 | ~90% | ~5 | ~19k | Municipios pequeños, baja criminalidad |
| 1 | ~2% | ~270 | ~567k | Ciudades grandes, alta criminalidad |
| 2 | ~7% | ~100 | ~273k | Ciudades medianas |
| 3 | ~1% | ~137 | ~1M | Área metropolitana Bucaramanga |

#### Uso

- Segmentar municipios para entrenar modelos específicos por tipo
- Análisis exploratorio de patrones geográficos

#### Ejecución

```bash
python scripts/04_generate_clustering_geo_dataset.py
```

---

## Resumen de Salidas

```
data/gold/
├── analytics/
│   └── gold_analytics.parquet              # Analytics enriquecido
├── dashboard/
│   ├── municipios.parquet                  # Geografía para dashboard
│   ├── poblacion_santander.parquet         # Población
│   ├── policia_santander.parquet           # Policía + temporales
│   ├── delitos_informaticos.parquet        # Delitos informáticos
│   ├── delitos_bucaramanga.parquet         # Socrata Bucaramanga
│   └── <metas>/*.parquet                   # Metas copiadas
└── model/
    ├── regression_monthly_dataset.parquet       # 9,143 filas
    ├── regression_annual_dataset.parquet        # 1,334 filas
    ├── regression_timeseries_dataset.parquet    # 190 filas
    ├── classification_monthly_dataset.parquet   # 9,143 filas
    ├── classification_event_dataset.parquet     # 279,762 filas
    ├── classification_dominant_dataset.parquet  # 33,408 filas
    └── clustering_geo_dataset.parquet           # 9,143 filas
```

---

## Niveles de Granularidad

| Nivel | Descripción | Datasets |
|-------|-------------|----------|
| **Mensual** | Una fila por municipio-mes | `regression_monthly_dataset`, `classification_monthly_dataset`, `clustering_geo_dataset` |
| **Anual** | Una fila por municipio-año | `regression_annual_dataset` |
| **Global** | Una fila por mes departamental | `regression_timeseries_dataset` |
| **Evento** | Una fila por delito individual | `classification_event_dataset` |
| **Agregado** | Delito/arma dominante por municipio-mes | `classification_dominant_dataset` |

---

## Ejecución Completa del Pipeline

```bash
# 1. Analytics y Dashboard (deben ejecutarse primero)
python scripts/04_generate_analytics.py
python scripts/04_generate_dashboard_data.py

# 2. Regresión
python scripts/04_generate_regression_monthly_dataset.py
python scripts/04_generate_regression_annual_dataset.py
python scripts/04_generate_regression_timeseries_dataset.py

# 3. Clasificación
python scripts/04_generate_classification_monthly_dataset.py
python scripts/04_generate_classification_event_dataset.py
python scripts/04_generate_classification_dominant_dataset.py

# 4. Clustering
python scripts/04_generate_clustering_geo_dataset.py
```

---

## Librerías Utilizadas

| Librería | Uso | Scripts |
|----------|-----|---------|
| `pandas` | Manipulación de datos | Todos |
| `numpy` | Cálculos numéricos, codificación cíclica | Todos |
| `geopandas` | Lectura de parquet con geometrías | Regresión |
| `scikit-learn` | KMeans para clustering | `04_generate_clustering_geo_dataset.py` |

---

## Modelos Recomendados

| Dataset | Tipo de Modelo | Algoritmos Sugeridos |
|---------|---------------|---------------------|
| `regression_monthly_dataset` | Regresión | XGBoost, LightGBM, Random Forest |
| `regression_annual_dataset` | Regresión espacial | XGBoost, modelos geoespaciales |
| `regression_timeseries_dataset` | Serie temporal | ARIMA, Prophet, LSTM |
| `classification_monthly_dataset` | Clasificación | XGBoost, Random Forest, SVM |
| `classification_event_dataset` | Multi-output | MultiOutputClassifier(XGBoost) |
| `classification_dominant_dataset` | Clasificación | Random Forest, XGBoost |
| `clustering_geo_dataset` | Segmentación | KMeans (ya aplicado), DBSCAN |
