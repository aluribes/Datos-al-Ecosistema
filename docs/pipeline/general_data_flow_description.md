# Flujo de Datos — Datos-al-Ecosistema

Este documento describe el flujo completo de transformación de datos desde la extracción hasta los datasets finales para analytics y modelado.

---

## Resumen del Pipeline

```
BRONZE          →    SILVER         →    GOLD           →    ANALYTICS      →    MODEL DATA     →    MODEL
01_* scripts         02_* scripts        03_* scripts        04_* scripts        05_* scripts        06_* scripts
                                                                  │
                                                                  ├──→ gold_analytics.parquet
                                                                  │         │
                                                                  │         ├──→ Dashboard (Power BI / Streamlit)
                                                                  │         │
                                                                  │         ├──→ regression_data.parquet ──→ regression_model.pkl ──→ Predicciones
                                                                  │         │
                                                                  │         └──→ classification_data.parquet ──→ classification_model.pkl
```

---

## 📊 Fase 1: Bronze (Extracción)

### Scripts y sus salidas

| Script | Fuente | Archivos Generados |
|--------|--------|-------------------|
| `01_extract_bronze.py` | Socrata API, DANE | `socrata_api/*.json`, `dane_geo/divipola_2010.xls` |
| `01_generate_polygon_santander.py` | GitHub GeoJSON | `dane_geo/santander_municipios.geojson` |
| `01_scrape_policia_estadistica.py` | Policía Nacional web | `policia_scraping/*.xlsx` (~241 archivos) |

### Columnas en Bronze (ejemplos)

**Policía (Excel crudo):**
- Encabezados variables según archivo: `DEPARTAMENTO`, `MUNICIPIO`, `CODIGO DANE`, `DELITO`, `FECHA`, `GENERO`, `ARMA MEDIO`, `CANTIDAD`, etc.

**GeoJSON Santander:**
- `DPTO_CCDGO`, `MPIO_CCNCT`, `MPIO_CNMBR`, `DPTO_CNMBR`, `MPIO_NAREA`, `geometry`

**DIVIPOLA:**
- `Código Departamento`, `Código Municipio`, `Código Centro Poblado`, `Nombre Departamento`, `Nombre Municipio`, etc.

---

## 🔧 Fase 2: Silver (Limpieza y Estandarización)

### Scripts y transformaciones

| Script | Entrada | Salida | Transformaciones Clave |
|--------|---------|--------|------------------------|
| `02_process_danegeo.py` | `divipola_2010.xls`, `santander_municipios.geojson` | `divipola_silver.parquet`, `geografia_silver.parquet` | Filtrar Santander, normalizar nombres, renombrar columnas |
| `02_process_policia.py` | `policia_scraping/*.xlsx` | `policia_santander.parquet` | Unificar 241 archivos, estandarizar columnas, filtrar Santander |
| `02_datos_poblacion_santander.py` | `TerriData_Pob_*.txt` | `poblacion_santander.parquet` | Clasificar edades, agregar por género |

### Columnas en Silver

**`geografia_silver.parquet`:**
| Columna | Tipo | Origen |
|---------|------|--------|
| `codigo_departamento` | str | DPTO_CCDGO |
| `codigo_municipio` | str | MPIO_CCNCT |
| `departamento` | str | DPTO_CNMBR (normalizado) |
| `municipio` | str | MPIO_CNMBR (normalizado) |
| `area` | float | MPIO_NAREA |
| `geometry` | geometry | geometry |

**`divipola_silver.parquet`:**
| Columna | Tipo | Origen |
|---------|------|--------|
| `codigo_departamento` | str | Código Departamento |
| `codigo_municipio` | str | Código Municipio |
| `codigo_centro_poblado` | str | Código Centro Poblado |
| `departamento` | str | Nombre Departamento |
| `municipio` | str | Nombre Municipio |
| `centro_poblado` | str | Nombre Centro Poblado |
| `clase` | str | Clase |

**`policia_santander.parquet`:**
| Columna | Tipo | Origen |
|---------|------|--------|
| `departamento` | str | Múltiples variantes unificadas |
| `municipio` | str | Múltiples variantes unificadas |
| `codigo_dane` | str | CODIGO DANE / CODIGO_DANE |
| `delito` | str | delito_archivo (renombrado, categorizado) |
| `edad_persona` | str | Variantes de edad agrupadas |
| `armas_medios` | str | Variantes unificadas |
| `cantidad` | int | CANTIDAD |
| `fecha` | datetime | FECHA / FECHA HECHO |
| `genero` | str | GENERO |
| `anio` | int | Extraído del nombre de archivo |

**`poblacion_santander.parquet`:**
| Columna | Tipo | Origen |
|---------|------|--------|
| `codigo_municipio` | str | Código Entidad |
| `anio` | int | Año |
| `genero` | str | MASCULINO / FEMENINO |
| `grupo_edad` | str | MENORES / ADOLESCENTES / ADULTOS |
| `n_poblacion` | int | Dato Numérico (agregado) |

---

## 🥇 Fase 3: Gold Base (Limpieza Final)

### Script: `03_process_silver_data.py`

Toma Silver y aplica limpieza final para Gold base. Usa la librería `holidays` para identificar festivos colombianos.

| Entrada | Salida | Transformaciones |
|---------|--------|------------------|
| `geografia_silver.parquet` | `geo_gold.parquet` | Reparar geometrías, normalizar códigos |
| `policia_santander.parquet` | `policia_gold.parquet` | Limpiar codigo_dane → codigo_municipio, extraer fecha, agregar columnas temporales y festivos |
| `poblacion_santander.parquet` | `poblacion_gold.parquet` | Normalizar tipos |
| `divipola_silver.parquet` | `divipola_gold.parquet` | Normalizar tipos |

### Columnas Generadas en `policia_gold.parquet`

| Columna Nueva | Tipo | Descripción |
|---------------|------|-------------|
| `codigo_municipio` | Int64 | Código DANE limpio (5 dígitos) |
| `anio` | Int64 | Año extraído de fecha |
| `mes` | Int64 | Mes extraído de fecha |
| `dia` | Int64 | Día extraído de fecha |
| `es_dia_semana` | int | 1 si Lunes-Viernes, 0 si fin de semana |
| `es_fin_de_semana` | int | 1 si Sábado-Domingo, 0 si día de semana |
| `es_fin_mes` | int | 1 si es el último día del mes |
| `es_festivo` | int | 1 si es festivo colombiano |
| `nombre_festivo` | str | Nombre del festivo o None |
| `es_dia_laboral` | int | 1 si es día de semana Y no es festivo |

> ✅ **Estas columnas a nivel de día** se usan para generar conteos mensuales en `gold_integrado`.

---

## 🏆 Fase 4: Gold Integrado

### Script: `03_generate_gold.py`

Combina todos los datasets Gold base en uno solo, agregando datos a nivel mensual.

### Proceso de Integración

```
geo_gold ──┬── merge (codigo_municipio) ──→ + divipola (n_centros_poblados)
           │
           ├── merge (codigo_municipio, anio, mes) ──→ + policia (delitos + conteos días)
           │
           └── merge (codigo_municipio, anio) ──→ + poblacion (demografía)
```

### Columnas en `gold_integrado.parquet`

| Categoría | Columnas |
|-----------|----------|
| **Identificadores** | `codigo_municipio`, `codigo_departamento`, `municipio`, `departamento` |
| **Temporales** | `anio`, `mes`, `fecha`, `trimestre`, `anio_mes`, `es_fin_ano` |
| **Conteos mensuales** | `n_dias_semana`, `n_fines_de_semana`, `n_festivos`, `n_dias_laborales`, `n_fines_mes` |
| **Geográficas** | `geometry`, `area`, `area_km2`, `Shape_Area`, `Shape_Leng` |
| **Densidad** | `densidad_poblacional`, `centros_por_km2`, `n_centros_poblados` |
| **Delitos (pivot)** | `HOMICIDIOS`, `HURTOS`, `LESIONES`, `VIOLENCIA INTRAFAMILIAR`, `AMENAZAS`, `DELITOS SEXUALES`, `EXTORSION`, `ABIGEATO`, `total_delitos` |
| **Población total** | `poblacion_total`, `poblacion_menores`, `poblacion_adolescentes`, `poblacion_adultos` |
| **Población género-edad** | `masculino_menores`, `masculino_adolescentes`, `masculino_adultos`, `femenino_menores`, `femenino_adolescentes`, `femenino_adultos` |
| **Proporciones** | `proporcion_menores`, `proporcion_adolescentes`, `proporcion_adultos` |

### Conteos Mensuales de Días

Las columnas `es_*` de `policia_gold` se agregan por `(codigo_municipio, anio, mes)`:

| Columna en Gold Integrado | Agregación desde policia_gold |
|---------------------------|------------------------------|
| `n_dias_semana` | `SUM(es_dia_semana)` — días Lunes-Viernes con delitos registrados |
| `n_fines_de_semana` | `SUM(es_fin_de_semana)` — días Sábado-Domingo con delitos registrados |
| `n_festivos` | `SUM(es_festivo)` — días festivos con delitos registrados |
| `n_dias_laborales` | `SUM(es_dia_laboral)` — días laborales con delitos registrados |
| `n_fines_mes` | `SUM(es_fin_mes)` — últimos días del mes con delitos registrados |

> ⚠️ **Nota**: Estos conteos reflejan días **con delitos registrados**, no el total de días del mes.

---

## 📈 Fase 5: Analytics

### Script: `04_generate_analytics.py`

Genera el dataset analítico enriquecido con tasas, variables temporales y features para modelado.

| Entrada | Salida |
|---------|--------|
| `gold_integrado.parquet` | `analytics/gold_analytics.parquet` |

### Columnas Generadas

#### Tasas por 100,000 habitantes

| Columna Nueva | Fórmula |
|---------------|---------|
| `tasa_homicidios` | `HOMICIDIOS / poblacion_total * 100000` |
| `tasa_hurtos` | `HURTOS / poblacion_total * 100000` |
| `tasa_lesiones` | `LESIONES / poblacion_total * 100000` |
| `tasa_violencia_intrafamiliar` | `VIOLENCIA INTRAFAMILIAR / poblacion_total * 100000` |
| `tasa_amenazas` | `AMENAZAS / poblacion_total * 100000` |
| `tasa_delitos_sexuales` | `DELITOS SEXUALES / poblacion_total * 100000` |
| `tasa_extorsion` | `EXTORSION / poblacion_total * 100000` |
| `tasa_abigeato` | `ABIGEATO / poblacion_total * 100000` |

#### Variables Cíclicas (Estacionalidad)

| Columna Nueva | Fórmula |
|---------------|---------|
| `mes_sin` | `sin(2π × mes / 12)` |
| `mes_cos` | `cos(2π × mes / 12)` |

#### Lags de `total_delitos`

| Columna Nueva | Descripción |
|---------------|-------------|
| `lag_1` | Delitos del mes anterior |
| `lag_3` | Delitos de hace 3 meses (trimestral) |
| `lag_12` | Delitos del mismo mes, año anterior |

#### Estadísticas Móviles

| Columna Nueva | Descripción |
|---------------|-------------|
| `roll_mean_3` | Promedio móvil últimos 3 meses |
| `roll_mean_12` | Promedio móvil últimos 12 meses |
| `roll_std_3` | Desviación estándar últimos 3 meses |
| `roll_std_12` | Desviación estándar últimos 12 meses |

#### Variaciones Porcentuales

| Columna Nueva | Descripción |
|---------------|-------------|
| `pct_change_1` | Cambio % vs mes anterior |
| `pct_change_3` | Cambio % vs hace 3 meses |
| `pct_change_12` | Cambio % vs mismo mes año anterior |

#### Columna Auxiliar

| Columna Nueva | Descripción |
|---------------|-------------|
| `fecha_proper` | Fecha como datetime (`anio_mes` parseado) |

> ✅ `gold_analytics.parquet` es el dataset central para visualización y modelado.

---

## 📊 Fase 6: Dashboard

### Script: `05_dashboard.py` (Streamlit / Power BI)

Visualización interactiva de datos para usuarios finales.

| Entrada | Salida |
|---------|--------|
| `analytics/gold_analytics.parquet` | Dashboard interactivo |

### Funcionalidades Esperadas

- Mapa de calor de delitos por municipio
- Series temporales de tasas de delitos
- Filtros por año, mes, municipio, tipo de delito
- Comparativas entre municipios
- Indicadores clave (KPIs) de seguridad

---

## 🤖 Fase 7: Model Data (Preparación)

### 7.1 Regression Data (Total Crimes)

#### Script: `04_generate_regression_total_crimes.py`

Prepara el dataset para modelos de regresión (predicción de cantidad de delitos).

| Entrada | Salida |
|---------|--------|
| `analytics/gold_analytics.parquet` | `model/regression_total_crimes.parquet` |

> **Estado:** ✅ Implementado

#### Transformaciones

1. Cargar `gold_analytics.parquet` (ya incluye lags, rolling stats, pct_change)
2. Eliminar columnas no numéricas:
   - `geometry`
   - `municipio`
   - `departamento`
   - `fecha_proper`
   - `anio_mes`

#### Implementación Actual

```python
def make_regression_dataset():
    df = pd.read_parquet(ANALYTICS)

    # eliminar columnas no numéricas / no útiles
    drop_cols = ["geometry", "municipio", "departamento", "fecha_proper", "anio_mes"]
    df = df.drop(columns=drop_cols, errors="ignore")

    df.to_parquet(OUT, index=False)
```

#### Columnas Disponibles

El dataset incluye todas las columnas numéricas de `gold_analytics.parquet`:
- Identificadores: `codigo_municipio`, `codigo_departamento`, `anio`, `mes`, `trimestre`
- Target: `total_delitos`
- Features demográficas: `poblacion_total`, `densidad_poblacional`, proporciones
- Features geográficas: `centros_por_km2`, `area_km2`, `n_centros_poblados`
- Variables cíclicas: `mes_sin`, `mes_cos`
- Lags: `lag_1`, `lag_3`, `lag_12`
- Rolling stats: `roll_mean_3`, `roll_mean_12`, `roll_std_3`, `roll_std_12`
- Variaciones: `pct_change_1`, `pct_change_3`, `pct_change_12`
- Tasas: `tasa_homicidios`, `tasa_hurtos`, etc.
- Delitos individuales: `HOMICIDIOS`, `HURTOS`, etc.

### 7.2 Classification Datasets (Riesgo + Incremento)

#### Script: `04_generate_classification_datasets.py`

Genera ambos datasets para modelos de clasificación en un solo script.

> **Estado:** ✅ Implementado

---

#### 7.2.1 Nivel de Riesgo (Multiclase)

| Entrada | Salida |
|---------|--------|
| `analytics/gold_analytics.parquet` | `model/classification_riesgo_dataset.parquet` |

**Transformaciones:**

1. Cargar `gold_analytics.parquet`
2. Crear variable target categórica: `nivel_riesgo`
   - **BAJO**: total_delitos <= percentil 33
   - **MEDIO**: percentil 33 < total_delitos <= percentil 66
   - **ALTO**: total_delitos > percentil 66
3. Eliminar columnas no numéricas (`geometry`, `municipio`, `departamento`, `fecha_proper`, `anio_mes`)

**Implementación:**

```python
def create_nivel_riesgo(series: pd.Series) -> pd.Series:
    p33 = series.quantile(0.33)
    p66 = series.quantile(0.66)
    
    conditions = [
        series <= p33,
        (series > p33) & (series <= p66),
        series > p66
    ]
    choices = ["BAJO", "MEDIO", "ALTO"]
    
    return pd.Series(
        np.select(conditions, choices, default="MEDIO"),
        index=series.index,
        dtype="category"
    )
```

**Columnas:** Todas las de `regression_total_crimes` + `nivel_riesgo` (categórica: BAJO/MEDIO/ALTO)

---

#### 7.2.2 Incremento de Delitos (Binaria)

| Entrada | Salida |
|---------|--------|
| `analytics/gold_analytics.parquet` | `model/classification_incremento_dataset.parquet` |

**Transformaciones:**

1. Cargar `gold_analytics.parquet`
2. Crear variable target binaria: `incremento_delitos`
   - **1**: Si `pct_change_1 > 0` (hubo incremento vs mes anterior)
   - **0**: Si `pct_change_1 <= 0` (se mantuvo o disminuyó)
3. Eliminar filas con NaN en `pct_change_1` (primer mes de cada municipio)
4. Eliminar columnas no numéricas

**Implementación:**

```python
def create_incremento_delitos(df: pd.DataFrame) -> pd.Series:
    return (df["pct_change_1"] > 0).astype(int)
```

**Columnas:** Todas las de `regression_total_crimes` + `incremento_delitos` (binaria: 0/1)

---

### 7.3 Classification Data (Weapons)

#### Script: `04_generate_classification_weapons.py`

Genera dataset para clasificación de tipo de delito o arma usada, enriquecido con contexto municipal.

| Entrada | Salida |
|---------|--------|
| `base/policia_gold.parquet` | `model/classification_weapons.parquet` |
| `gold_integrado.parquet` | |

> **Estado:** ✅ Implementado

#### Transformaciones

1. Cargar `policia_gold.parquet` (datos por evento individual)
2. Cargar `gold_integrado.parquet` (contexto demográfico mensual)
3. Merge LEFT por `(codigo_municipio, anio, mes)` para enriquecer cada delito
4. Agregar codificación cíclica del mes (`mes_sin`, `mes_cos`)
5. Convertir targets a categóricos: `delito`, `armas_medios`

#### Implementación

```python
def build_classification_dataset(df_pol, df_int):
    # Merge para enriquecer cada delito con su contexto mensual
    df = df_pol.merge(
        df_int,
        on=["codigo_municipio", "anio", "mes"],
        how="left",
        suffixes=("", "_ctx")
    )
    
    # Codificación cíclica del mes
    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)
    
    # Variables objetivo categóricas
    df["delito"] = df["delito"].astype("category")
    df["armas_medios"] = df["armas_medios"].astype("category")
    
    return df
```

#### Columnas del Dataset

| Categoría | Columnas |
|-----------|----------|
| **Targets** | `delito` (categórica), `armas_medios` (categórica) |
| **Evento** | `genero`, `edad_persona`, `es_festivo`, `es_dia_semana`, `es_fin_de_semana`, etc. |
| **Contexto municipal** | Todas las columnas de `gold_integrado` (población, densidad, tasas, etc.) |
| **Temporales** | `anio`, `mes`, `mes_sin`, `mes_cos`, `trimestre` |

> 💡 Este dataset está a **nivel de evento** (cada fila = un delito), a diferencia de los otros que están a nivel mensual.

---

## 🎯 Fase 8: Model Training

### 8.1 Regression Model

#### Script: `06_train_regression_model.py`

Entrena modelo de regresión para predecir cantidad de delitos.

| Entrada | Salida |
|---------|--------|
| `model/regression_data.parquet` | `model/regression_model.pkl` |

#### Proceso

1. Cargar `regression_data.parquet`
2. Split train/test (temporal split recomendado)
3. Entrenar modelo (XGBoost, LightGBM, Random Forest, etc.)
4. Evaluar métricas (MAE, RMSE, R²)
5. Guardar modelo entrenado

#### Métricas Esperadas

| Métrica | Descripción |
|---------|-------------|
| MAE | Error absoluto medio |
| RMSE | Raíz del error cuadrático medio |
| R² | Coeficiente de determinación |
| MAPE | Error porcentual absoluto medio |

### 8.2 Classification Model

#### Script: `06_train_classification_model.py`

Entrena modelo de clasificación para predecir nivel de riesgo.

| Entrada | Salida |
|---------|--------|
| `model/classification_data.parquet` | `model/classification_model.pkl` |

#### Proceso

1. Cargar `classification_data.parquet`
2. Split train/test (temporal split recomendado)
3. Entrenar modelo (XGBoost, LightGBM, Random Forest, etc.)
4. Evaluar métricas (Accuracy, F1, Precision, Recall)
5. Guardar modelo entrenado

#### Métricas Esperadas

| Métrica | Descripción |
|---------|-------------|
| Accuracy | Precisión general |
| F1-Score | Balance precision/recall |
| Precision | Precisión por clase |
| Recall | Sensibilidad por clase |
| Confusion Matrix | Matriz de confusión |

---

## 🔮 Fase 9: Predicciones

### Script: `07_predict.py`

Genera predicciones usando los modelos entrenados.

| Entrada | Salida |
|---------|--------|
| `model/regression_model.pkl` | Predicciones de delitos |
| `model/classification_model.pkl` | Predicciones de riesgo |
| Datos nuevos (próximo mes) | |

#### Proceso

1. Cargar modelo entrenado
2. Preparar datos de entrada (mismo preprocesamiento que entrenamiento)
3. Generar predicciones
4. Formatear resultados para visualización

#### Salidas

| Archivo | Descripción |
|---------|-------------|
| `predictions/predicciones_regresion.parquet` | Predicciones numéricas por municipio-mes |
| `predictions/predicciones_clasificacion.parquet` | Niveles de riesgo por municipio-mes |

---

## 📋 Resumen de Archivos del Pipeline

### Datasets por Fase

| Fase | Archivo | Descripción | Estado |
|------|---------|-------------|--------|
| Silver | `policia_santander.parquet` | Delitos limpios | ✅ |
| Silver | `geografia_silver.parquet` | Geografía limpia | ✅ |
| Silver | `poblacion_santander.parquet` | Población limpia | ✅ |
| Gold Base | `policia_gold.parquet` | Delitos con fechas y festivos | ✅ |
| Gold Base | `geo_gold.parquet` | Geografía normalizada | ✅ |
| Gold Integrado | `gold_integrado.parquet` | Dataset mensual consolidado | ✅ |
| Analytics | `gold_analytics.parquet` | Dataset con tasas, lags, rolling stats | ✅ |
| Model | `regression_total_crimes.parquet` | Features para regresión (mensual) | ✅ |
| Model | `classification_riesgo_dataset.parquet` | Clasificación multiclase (BAJO/MEDIO/ALTO) | ✅ |
| Model | `classification_incremento_dataset.parquet` | Clasificación binaria (incremento 0/1) | ✅ |
| Model | `classification_weapons.parquet` | Clasificación por evento (arma/delito) | ✅ |
| Model | `regression_model.pkl` | Modelo de regresión entrenado | ⏳ |
| Model | `classification_model.pkl` | Modelo de clasificación entrenado | ⏳ |
| Predictions | `predicciones_*.parquet` | Predicciones finales | ⏳ |

### Scripts por Fase

| Fase | Script | Función | Estado |
|------|--------|---------|--------|
| 01 Bronze | `01_extract_bronze.py` | Extracción de APIs | ✅ |
| 01 Bronze | `01_generate_polygon_santander.py` | Descarga GeoJSON | ✅ |
| 01 Bronze | `01_scrape_policia_estadistica.py` | Scraping policía | ✅ |
| 02 Silver | `02_process_danegeo.py` | Limpieza geografía | ✅ |
| 02 Silver | `02_process_policia.py` | Limpieza policía | ✅ |
| 02 Silver | `02_datos_poblacion_santander.py` | Limpieza población | ✅ |
| 03 Gold | `03_process_silver_data.py` | Gold base | ✅ |
| 03 Gold | `03_generate_gold.py` | Gold integrado | ✅ |
| 04 Analytics | `04_generate_analytics.py` | Tasas + lags + rolling | ✅ |
| 04 Model Data | `04_generate_regression_total_crimes.py` | Regresión total delitos | ✅ |
| 04 Model Data | `04_generate_classification_datasets.py` | Clasificación riesgo + incremento | ✅ |
| 04 Model Data | `04_generate_classification_weapons.py` | Clasificación armas/delitos | ✅ |
| 05 Dashboard | `05_dashboard.py` | Visualización | ⏳ |
| 06 Training | `06_train_regression_model.py` | Entrenar regresión | ⏳ |
| 06 Training | `06_train_classification_model.py` | Entrenar clasificación | ⏳ |
| 07 Predict | `07_predict.py` | Generar predicciones | ⏳ |

---

## 📋 Resumen de Columnas Finales

### `gold_analytics.parquet` (dataset central)

| Categoría | Columnas |
|-----------|----------|
| **Identificadores** | `codigo_municipio`, `codigo_departamento`, `municipio`, `departamento` |
| **Temporales** | `anio`, `mes`, `fecha`, `trimestre`, `anio_mes`, `es_fin_ano`, `fecha_proper` |
| **Conteos mensuales** | `n_dias_semana`, `n_fines_de_semana`, `n_festivos`, `n_dias_laborales`, `n_fines_mes` |
| **Geográficas** | `geometry`, `area_km2` |
| **Densidad** | `densidad_poblacional`, `centros_por_km2`, `n_centros_poblados` |
| **Delitos** | `total_delitos`, `HOMICIDIOS`, `HURTOS`, `LESIONES`, `VIOLENCIA INTRAFAMILIAR`, `AMENAZAS`, `DELITOS SEXUALES`, `EXTORSION`, `ABIGEATO` |
| **Tasas** | `tasa_homicidios`, `tasa_hurtos`, `tasa_lesiones`, `tasa_violencia_intrafamiliar`, `tasa_amenazas`, `tasa_delitos_sexuales`, `tasa_extorsion`, `tasa_abigeato` |
| **Variables cíclicas** | `mes_sin`, `mes_cos` |
| **Lags** | `lag_1`, `lag_3`, `lag_12` |
| **Rolling stats** | `roll_mean_3`, `roll_mean_12`, `roll_std_3`, `roll_std_12` |
| **Variaciones %** | `pct_change_1`, `pct_change_3`, `pct_change_12` |
| **Población** | `poblacion_total`, `poblacion_menores`, `poblacion_adolescentes`, `poblacion_adultos` |
| **Proporciones** | `proporcion_menores`, `proporcion_adolescentes`, `proporcion_adultos` |

### `regression_total_crimes.parquet` (para ML regresión)

Todo lo de `gold_analytics` excepto: `geometry`, `municipio`, `departamento`, `fecha_proper`, `anio_mes`.

### `classification_riesgo_dataset.parquet` (para ML clasificación multiclase)

Todo lo de `regression_total_crimes` + `nivel_riesgo` (categórica: BAJO/MEDIO/ALTO basado en percentiles 33/66).

### `classification_incremento_dataset.parquet` (para ML clasificación binaria)

Todo lo de `regression_total_crimes` + `incremento_delitos` (binaria: 0/1 si `pct_change_1 > 0`).

### `classification_weapons.parquet` (para ML clasificación por evento)

Dataset a nivel de evento individual (cada fila = un delito):
- **Targets:** `delito` (categórica), `armas_medios` (categórica)
- **Evento:** Columnas de `policia_gold` (genero, edad, festivo, día semana, etc.)
- **Contexto:** Columnas de `gold_integrado` (población, densidad, tasas, delitos agregados)
- **Temporales:** `mes_sin`, `mes_cos` (codificación cíclica)

---

## 🔧 Dependencias Clave

| Librería | Uso | Scripts |
|----------|-----|---------|
| `holidays` | Festivos colombianos | `03_process_silver_data.py` |
| `geopandas` | Geometrías | `03_process_silver_data.py`, `03_generate_gold.py` |
| `pandas` | Transformaciones | Todos |
| `numpy` | Cálculos numéricos, variables cíclicas | `04_generate_*_data.py` |
| `scikit-learn` | Modelos ML, métricas | `06_train_*.py` |
| `xgboost` / `lightgbm` | Modelos gradient boosting | `06_train_*.py` |
| `streamlit` | Dashboard interactivo | `05_dashboard.py` |
| `joblib` / `pickle` | Serialización de modelos | `06_train_*.py`, `07_predict.py` |

---

## 🎯 Decisiones de Diseño

### ¿Por qué columnas de día en `policia_gold`?

Las columnas `es_dia_semana`, `es_fin_de_semana`, `es_festivo`, `es_dia_laboral`, `es_fin_mes` se generan a **nivel de registro individual** (cada delito) en `policia_gold`. Esto permite:

1. Mantener granularidad en Gold Base para posibles análisis futuros
2. Agregar a nivel mensual en `gold_integrado` mediante `SUM()`
3. Evitar duplicar la lógica de festivos (solo se calcula una vez con `holidays`)

### ¿Por qué agregación mensual en `gold_integrado`?

El dataset final está a nivel `municipio × año × mes` porque:
- Los análisis y dashboards se hacen a nivel mensual
- El modelo predictivo predice delitos mensuales
- No hay suficiente granularidad para predicciones diarias

### ¿Qué representan los conteos mensuales?

Los conteos `n_dias_semana`, `n_festivos`, etc. representan **días con delitos registrados**, no el calendario completo del mes. Esto captura la distribución temporal de los delitos.
