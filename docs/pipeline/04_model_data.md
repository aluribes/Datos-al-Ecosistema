# Capa Model Data — Preparación para Machine Learning

La capa Model Data contiene los datasets optimizados para entrenamiento de modelos de Machine Learning. Se generan a partir de `gold_analytics.parquet` (nivel mensual) y `policia_gold.parquet` (nivel evento).

## Scripts de generación

| Script | Entrada | Salida | Tipo |
|--------|---------|--------|------|
| `04_generate_regression_total_crimes.py` | Analytics | Regresión total delitos | Mensual |
| `04_generate_regression_per_crime.py` | Analytics | Regresión por tipo de delito | Mensual |
| `04_generate_regression_geo.py` | Gold integrado | Regresión geográfica | Anual |
| `04_generate_global_regression.py` | Analytics | Regresión serie temporal global | Mensual |
| `04_generate_classification_datasets.py` | Analytics | Riesgo + Incremento | Mensual |
| `04_generate_classification_risk.py` | Gold integrado | Nivel de riesgo | Mensual |
| `04_generate_classification_crime.py` | Policía + Gold | Tipo de delito | Evento |
| `04_generate_classification_weapon.py` | Policía + Gold | Tipo de arma | Evento |
| `04_generate_classification_profile.py` | Policía + Gold | Perfil demográfico | Evento |
| `04_generate_classification_cluster.py` | Policía + Gold | Clusters y dominantes | Mixto |

---

## Datasets de Regresión

### 1. Regresión de Total de Delitos

**Script:** `scripts/04_generate_regression_total_crimes.py`

Dataset principal para predecir la cantidad total de delitos por municipio-mes.

#### Transformaciones

- Carga `gold_analytics.parquet`
- Elimina columnas no numéricas: `geometry`, `municipio`, `departamento`, `fecha_proper`, `anio_mes`
- Mantiene todas las features numéricas para ML

#### Ejecución

```bash
python scripts/04_generate_regression_total_crimes.py
```

#### Salida

```
data/gold/model/
└── regression_total_crimes.parquet
```

#### Columnas principales

| Categoría | Columnas |
|-----------|----------|
| **Target** | `total_delitos` |
| **Identificadores** | `codigo_municipio`, `codigo_departamento`, `anio`, `mes`, `trimestre` |
| **Demográficas** | `poblacion_total`, `densidad_poblacional`, proporciones |
| **Geográficas** | `area_km2`, `centros_por_km2`, `n_centros_poblados` |
| **Temporales** | `mes_sin`, `mes_cos`, `n_festivos`, `n_dias_laborales` |
| **Lags** | `lag_1`, `lag_3`, `lag_12` |
| **Rolling** | `roll_mean_3`, `roll_mean_12`, `roll_std_3`, `roll_std_12` |
| **Variaciones** | `pct_change_1`, `pct_change_3`, `pct_change_12` |

---

### 2. Regresión por Tipo de Delito

**Script:** `scripts/04_generate_regression_per_crime.py`

Dataset para predecir tasas de delitos específicos (homicidios, hurtos, etc.).

#### Transformaciones

- Carga `gold_analytics.parquet`
- Selecciona features predictoras clave
- Incluye todas las tasas como variables objetivo (multioutput)

#### Ejecución

```bash
python scripts/04_generate_regression_per_crime.py
```

#### Salida

```
data/gold/model/
└── regression_per_crime.parquet
```

#### Columnas

| Tipo | Columnas |
|------|----------|
| **Targets** | `tasa_homicidios`, `tasa_hurtos`, `tasa_lesiones`, `tasa_violencia_intrafamiliar`, `tasa_amenazas`, `tasa_delitos_sexuales`, `tasa_extorsion`, `tasa_abigeato` |
| **Features** | Demográficas, espaciales, temporales, lags, rolling |

---

### 3. Regresión Geográfica

**Script:** `scripts/04_generate_regression_geo.py`

Dataset agregado a nivel anual para análisis espacial y comparativas entre municipios.

#### Transformaciones

- Carga `gold_integrado.parquet`
- Agrupa por `(codigo_municipio, anio)` con suma anual de delitos
- Calcula tasas anuales por tipo de delito
- Promedia variables demográficas

#### Ejecución

```bash
python scripts/04_generate_regression_geo.py
```

#### Salida

```
data/gold/model/
└── regression_geo.parquet
```

#### Columnas

| Categoría | Columnas |
|-----------|----------|
| **Identificadores** | `codigo_municipio`, `anio` |
| **Targets** | `total_delitos`, tasas anuales por delito |
| **Features** | `poblacion_total`, `area_km2`, `densidad_poblacional`, `centros_por_km2` |

---

### 4. Regresión Serie Temporal Global

**Script:** `scripts/04_generate_global_regression.py`

Dataset con la serie temporal agregada del departamento completo.

#### Transformaciones

- Carga `gold_analytics.parquet`
- Agrupa por `anio_mes` sumando todos los municipios
- Calcula lags, rolling y pct_change sobre la serie global
- Añade codificación cíclica del mes

#### Ejecución

```bash
python scripts/04_generate_global_regression.py
```

#### Salida

```
data/gold/model/
└── multi_regression.parquet
```

#### Columnas

| Tipo | Columnas |
|------|----------|
| **Target** | `total_delitos`, `tasa_global` |
| **Temporales** | `fecha`, `mes`, `mes_sin`, `mes_cos` |
| **Lags** | `lag_1`, `lag_3`, `lag_12` |
| **Rolling** | `roll_3`, `roll_12` |
| **Variaciones** | `pct_change_1`, `pct_change_12` |

---

## Datasets de Clasificación

### 5. Clasificación de Nivel de Riesgo (Multiclase)

**Script:** `scripts/04_generate_classification_datasets.py`

Clasifica municipios-mes en niveles de riesgo: BAJO, MEDIO, ALTO.

#### Lógica de clasificación

```
BAJO:  total_delitos <= percentil 33
MEDIO: percentil 33 < total_delitos <= percentil 66
ALTO:  total_delitos > percentil 66
```

#### Ejecución

```bash
python scripts/04_generate_classification_datasets.py
```

#### Salida

```
data/gold/model/
└── classification_riesgo_dataset.parquet
```

#### Columnas

Todas las de `regression_total_crimes` + `nivel_riesgo` (categórica: BAJO/MEDIO/ALTO).

---

### 6. Clasificación de Incremento (Binaria)

**Script:** `scripts/04_generate_classification_datasets.py`

Predice si los delitos aumentaron vs el mes anterior.

#### Lógica de clasificación

```
1: pct_change_1 > 0 (hubo incremento)
0: pct_change_1 <= 0 (se mantuvo o disminuyó)
```

#### Salida

```
data/gold/model/
└── classification_incremento_dataset.parquet
```

#### Columnas

Todas las de `regression_total_crimes` + `incremento_delitos` (binaria: 0/1).

---

### 7. Clasificación de Riesgo Mensual (Alternativa)

**Script:** `scripts/04_generate_classification_risk.py`

Versión alternativa que usa `pd.qcut` para clasificación balanceada.

#### Ejecución

```bash
python scripts/04_generate_classification_risk.py
```

#### Salida

```
data/gold/model/
└── classification_risk_monthly.parquet
```

---

### 8. Clasificación de Tipo de Delito (Nivel Evento)

**Script:** `scripts/04_generate_classification_crime.py`

Predice qué tipo de delito ocurrirá dado el contexto del municipio.

#### Transformaciones

- Carga `policia_gold.parquet` (cada fila = un evento)
- Enriquece con contexto de `gold_integrado.parquet`
- Merge por `(codigo_municipio, anio, mes)`
- Añade codificación cíclica del mes

#### Ejecución

```bash
python scripts/04_generate_classification_crime.py
```

#### Salida

```
data/gold/model/
└── classification_crime_type.parquet
```

#### Columnas

| Tipo | Columnas |
|------|----------|
| **Target** | `delito` (categórica) |
| **Evento** | `genero`, `edad_persona`, `armas_medios`, `es_festivo`, `es_dia_semana` |
| **Contexto** | Todas las columnas de `gold_integrado` (población, densidad, tasas) |
| **Temporales** | `mes_sin`, `mes_cos` |

---

### 9. Clasificación de Tipo de Arma (Nivel Evento)

**Script:** `scripts/04_generate_classification_weapon.py`

Predice qué arma/medio se usará dado el delito y contexto.

#### Ejecución

```bash
python scripts/04_generate_classification_weapon.py
```

#### Salida

```
data/gold/model/
└── classification_weapon_type.parquet
```

#### Columnas

| Tipo | Columnas |
|------|----------|
| **Target** | `armas_medios` (categórica) |
| **Evento** | `delito`, `genero`, `edad_persona`, flags temporales |
| **Contexto** | Columnas de `gold_integrado` |

---

### 10. Clasificación de Perfil Demográfico (Nivel Evento)

**Script:** `scripts/04_generate_classification_profile.py`

Predice el perfil de persona involucrada (género + edad).

#### Transformaciones

- Crea variable `perfil = genero + "_" + edad_persona`
- Ejemplo: `MASCULINO_ADULTOS`, `FEMENINO_ADOLESCENTES`

#### Ejecución

```bash
python scripts/04_generate_classification_profile.py
```

#### Salida

```
data/gold/model/
└── classification_profile.parquet
```

---

### 11. Clasificaciones Auxiliares (Clusters y Dominantes)

**Script:** `scripts/04_generate_classification_cluster.py`

Genera múltiples datasets secundarios:

#### Salidas

```
data/gold/model/
├── classification_dominant_crime.parquet   # Delito más frecuente por municipio-mes
├── classification_dominant_weapon.parquet  # Arma más frecuente por municipio-mes
└── classification_geo_clusters.parquet     # Clusters de municipios (KMeans k=4)
```

#### Delito/Arma Dominante

Para cada `(codigo_municipio, anio, mes)`, identifica el delito/arma con mayor frecuencia.

#### Clusters Geográficos

Agrupa municipios usando KMeans (k=4) sobre:
- `total_delitos`
- `poblacion_total`
- `densidad_poblacional`

#### Ejecución

```bash
python scripts/04_generate_classification_cluster.py
```

---

## Resumen de Salidas Model Data

```
data/gold/model/
├── regression_total_crimes.parquet          # Regresión total delitos (mensual)
├── regression_per_crime.parquet             # Regresión por tipo de delito (mensual)
├── regression_geo.parquet                   # Regresión geográfica (anual)
├── multi_regression.parquet                 # Regresión serie temporal global
├── classification_riesgo_dataset.parquet    # Nivel riesgo multiclase
├── classification_incremento_dataset.parquet # Incremento binario
├── classification_risk_monthly.parquet      # Riesgo alternativo (qcut)
├── classification_crime_type.parquet        # Tipo de delito (evento)
├── classification_weapon_type.parquet       # Tipo de arma (evento)
├── classification_profile.parquet           # Perfil demográfico (evento)
├── classification_dominant_crime.parquet    # Delito dominante
├── classification_dominant_weapon.parquet   # Arma dominante
└── classification_geo_clusters.parquet      # Clusters geográficos
```

---

## Niveles de Granularidad

| Nivel | Descripción | Datasets |
|-------|-------------|----------|
| **Mensual** | Una fila por municipio-mes | `regression_total_crimes`, `regression_per_crime`, `classification_riesgo_dataset`, `classification_incremento_dataset`, `classification_risk_monthly` |
| **Anual** | Una fila por municipio-año | `regression_geo` |
| **Global** | Una fila por mes departamental | `multi_regression` |
| **Evento** | Una fila por delito individual | `classification_crime_type`, `classification_weapon_type`, `classification_profile` |
| **Agregado** | Delito/arma dominante por municipio-mes | `classification_dominant_crime`, `classification_dominant_weapon` |

---

## Ejecución Completa del Pipeline Model Data

Para generar todos los datasets de ML:

```bash
# Regresión
python scripts/04_generate_regression_total_crimes.py
python scripts/04_generate_regression_per_crime.py
python scripts/04_generate_regression_geo.py
python scripts/04_generate_global_regression.py

# Clasificación
python scripts/04_generate_classification_datasets.py
python scripts/04_generate_classification_risk.py
python scripts/04_generate_classification_crime.py
python scripts/04_generate_classification_weapon.py
python scripts/04_generate_classification_profile.py
python scripts/04_generate_classification_cluster.py
```

---

## Librerías Utilizadas

| Librería | Uso | Scripts |
|----------|-----|---------|
| `pandas` | Manipulación de datos | Todos |
| `numpy` | Cálculos numéricos, codificación cíclica | Todos |
| `geopandas` | Lectura de parquet con geometrías | Regresión |
| `scikit-learn` | KMeans para clustering | `04_generate_classification_cluster.py` |

---

## Siguiente Paso

Con los datasets preparados, el siguiente paso es entrenar modelos predictivos. Consulta la documentación de entrenamiento para:

- **Regresión**: Predecir cantidad de delitos con XGBoost, LightGBM, Random Forest
- **Clasificación**: Predecir nivel de riesgo con clasificadores multiclase
- **Serie temporal**: Predecir tendencia departamental con ARIMA, Prophet
