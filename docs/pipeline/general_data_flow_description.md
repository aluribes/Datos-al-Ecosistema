# Flujo de Datos — Datos-al-Ecosistema

Este documento describe el flujo completo de transformación de datos desde la extracción hasta los datasets finales para analytics y modelado.

---

## Resumen del Pipeline

```
BRONZE          →    SILVER         →    GOLD           →    ANALYTICS/MODEL DATA
01_* scripts         02_* scripts        03_* scripts        04_* scripts
                                                                  │
                                                                  ├──→ gold_analytics.parquet ──→ Dashboard
                                                                  │
                                                                  ├──→ REGRESIÓN (4 datasets)
                                                                  │    ├── regression_total_crimes.parquet
                                                                  │    ├── regression_per_crime.parquet
                                                                  │    ├── regression_geo.parquet
                                                                  │    └── multi_regression.parquet
                                                                  │
                                                                  └──→ CLASIFICACIÓN (9 datasets)
                                                                       ├── classification_riesgo_dataset.parquet
                                                                       ├── classification_incremento_dataset.parquet
                                                                       ├── classification_risk_monthly.parquet
                                                                       ├── classification_crime_type.parquet
                                                                       ├── classification_weapon_type.parquet
                                                                       ├── classification_profile.parquet
                                                                       ├── classification_dominant_crime.parquet
                                                                       ├── classification_dominant_weapon.parquet
                                                                       └── classification_geo_clusters.parquet
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

## 🤖 Fase 6: Model Data (Preparación para ML)

Los scripts `04_generate_*` generan datasets optimizados para Machine Learning. Ver [04_model_data.md](04_model_data.md) para documentación detallada.

### Resumen de Datasets Generados

#### Datasets de Regresión

| Script | Salida | Nivel | Descripción |
|--------|--------|-------|-------------|
| `04_generate_regression_total_crimes.py` | `regression_total_crimes.parquet` | Mensual | Predicción de total de delitos |
| `04_generate_regression_per_crime.py` | `regression_per_crime.parquet` | Mensual | Predicción de tasas por tipo de delito |
| `04_generate_regression_geo.py` | `regression_geo.parquet` | Anual | Análisis espacial agregado |
| `04_generate_global_regression.py` | `multi_regression.parquet` | Global | Serie temporal departamental |

#### Datasets de Clasificación

| Script | Salida | Target | Descripción |
|--------|--------|--------|-------------|
| `04_generate_classification_datasets.py` | `classification_riesgo_dataset.parquet` | `nivel_riesgo` | BAJO/MEDIO/ALTO (percentiles) |
| `04_generate_classification_datasets.py` | `classification_incremento_dataset.parquet` | `incremento_delitos` | Binaria 0/1 |
| `04_generate_classification_risk.py` | `classification_risk_monthly.parquet` | `riesgo` | Alternativa con qcut |
| `04_generate_classification_crime.py` | `classification_crime_type.parquet` | `delito` | Nivel evento |
| `04_generate_classification_weapon.py` | `classification_weapon_type.parquet` | `armas_medios` | Nivel evento |
| `04_generate_classification_profile.py` | `classification_profile.parquet` | `perfil` | Género + edad |
| `04_generate_classification_cluster.py` | `classification_dominant_crime.parquet` | `delito` | Delito dominante |
| `04_generate_classification_cluster.py` | `classification_dominant_weapon.parquet` | `armas_medios` | Arma dominante |
| `04_generate_classification_cluster.py` | `classification_geo_clusters.parquet` | `cluster_delictivo` | Clusters KMeans |

### Ejecución Completa

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
| Model (Regresión) | `regression_total_crimes.parquet` | Regresión total delitos (mensual) | ✅ |
| Model (Regresión) | `regression_per_crime.parquet` | Regresión por tipo de delito | ✅ |
| Model (Regresión) | `regression_geo.parquet` | Regresión geográfica (anual) | ✅ |
| Model (Regresión) | `multi_regression.parquet` | Serie temporal global departamento | ✅ |
| Model (Clasificación) | `classification_riesgo_dataset.parquet` | Nivel de riesgo (BAJO/MEDIO/ALTO) | ✅ |
| Model (Clasificación) | `classification_incremento_dataset.parquet` | Incremento binario (0/1) | ✅ |
| Model (Clasificación) | `classification_risk_monthly.parquet` | Riesgo mensual (alternativo) | ✅ |
| Model (Clasificación) | `classification_crime_type.parquet` | Tipo de delito (nivel evento) | ✅ |
| Model (Clasificación) | `classification_weapon_type.parquet` | Tipo de arma (nivel evento) | ✅ |
| Model (Clasificación) | `classification_profile.parquet` | Perfil demográfico (nivel evento) | ✅ |
| Model (Clasificación) | `classification_dominant_crime.parquet` | Delito dominante por municipio-mes | ✅ |
| Model (Clasificación) | `classification_dominant_weapon.parquet` | Arma dominante por municipio-mes | ✅ |
| Model (Clasificación) | `classification_geo_clusters.parquet` | Clusters de municipios (KMeans) | ✅ |

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
| 04 Model Data | `04_generate_regression_per_crime.py` | Regresión por tipo de delito | ✅ |
| 04 Model Data | `04_generate_regression_geo.py` | Regresión geográfica anual | ✅ |
| 04 Model Data | `04_generate_global_regression.py` | Serie temporal global | ✅ |
| 04 Model Data | `04_generate_classification_datasets.py` | Riesgo + incremento | ✅ |
| 04 Model Data | `04_generate_classification_risk.py` | Riesgo mensual alternativo | ✅ |
| 04 Model Data | `04_generate_classification_crime.py` | Tipo de delito (evento) | ✅ |
| 04 Model Data | `04_generate_classification_weapon.py` | Tipo de arma (evento) | ✅ |
| 04 Model Data | `04_generate_classification_profile.py` | Perfil demográfico | ✅ |
| 04 Model Data | `04_generate_classification_cluster.py` | Clusters y dominantes | ✅ |

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

### Datasets de Regresión

| Dataset | Nivel | Target | Descripción |
|---------|-------|--------|-------------|
| `regression_total_crimes.parquet` | Mensual | `total_delitos` | Features numéricas de analytics sin geometrías |
| `regression_per_crime.parquet` | Mensual | Tasas por delito | Predicción multi-output por tipo de delito |
| `regression_geo.parquet` | Anual | `total_delitos` + tasas | Agregado anual para análisis espacial |
| `multi_regression.parquet` | Global | `total_delitos` | Serie temporal departamental agregada |

### Datasets de Clasificación

| Dataset | Nivel | Target | Descripción |
|---------|-------|--------|-------------|
| `classification_riesgo_dataset.parquet` | Mensual | `nivel_riesgo` | BAJO/MEDIO/ALTO basado en percentiles 33/66 |
| `classification_incremento_dataset.parquet` | Mensual | `incremento_delitos` | Binaria 0/1 si `pct_change_1 > 0` |
| `classification_risk_monthly.parquet` | Mensual | `riesgo` | Alternativa con `pd.qcut` balanceado |
| `classification_crime_type.parquet` | Evento | `delito` | Tipo de delito con contexto municipal |
| `classification_weapon_type.parquet` | Evento | `armas_medios` | Tipo de arma/medio usado |
| `classification_profile.parquet` | Evento | `perfil` | Género + edad (ej: MASCULINO_ADULTOS) |
| `classification_dominant_crime.parquet` | Mensual | `delito` | Delito más frecuente por municipio-mes |
| `classification_dominant_weapon.parquet` | Mensual | `armas_medios` | Arma más frecuente por municipio-mes |
| `classification_geo_clusters.parquet` | Mensual | `cluster_delictivo` | Cluster KMeans (k=4) de municipios |

---

## 🔧 Dependencias Clave

| Librería | Uso | Scripts |
|----------|-----|---------|
| `holidays` | Festivos colombianos | `03_process_silver_data.py` |
| `geopandas` | Geometrías y datos espaciales | `03_*.py`, `04_generate_*.py` |
| `pandas` | Transformaciones de datos | Todos |
| `numpy` | Cálculos numéricos, codificación cíclica | `04_generate_*.py` |
| `scikit-learn` | KMeans para clustering | `04_generate_classification_cluster.py` |

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
