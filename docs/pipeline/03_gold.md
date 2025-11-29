# Capa Gold — Integración y Análisis

La capa Gold contiene los datos integrados y listos para análisis o modelado. Aquí se combinan todas las fuentes de Silver en datasets unificados.

## Scripts de integración

| Script | Entrada | Salida | Orden |
|--------|---------|--------|-------|
| `03_process_silver_data.py` | Silver: todos | Gold/base: datasets limpios | 1 |
| `03_generate_gold.py` | Gold/base | Gold: dataset integrado | 2 |
| `04_generate_analytics.py` | Gold integrado | Gold/analytics: indicadores | 3 |

---

## 1. Preparación Gold Base

**Script:** `scripts/03_process_silver_data.py`

Aplica limpieza final a los datos Silver y los prepara para integración. También **complementa datos faltantes** de Policía con datos de Socrata.

### Transformaciones aplicadas

- Verificación de existencia de archivos Silver
- Limpieza de geometrías (reparación de polígonos inválidos)
- Normalización de nombres de municipios
- Estandarización de códigos DANE
- Conversión de tipos de datos
- **Generación de columnas temporales y festivos** (policia_gold y socrata_gold)
- **Complementación de gaps** en datos de Policía con Socrata:
  - DELITOS SEXUALES 2021 (faltante en Policía)
  - HURTOS 2022 (incompleto en Policía)

### Columnas temporales generadas

| Columna | Descripción |
|---------|-------------|
| `es_dia_semana` | 1 si es lunes-viernes, 0 si no |
| `es_fin_de_semana` | 1 si es sábado o domingo, 0 si no |
| `es_festivo` | 1 si es festivo colombiano, 0 si no |
| `nombre_festivo` | Nombre del festivo o cadena vacía |
| `es_dia_laboral` | 1 si es día hábil (no festivo ni fin de semana) |
| `origen` | Trazabilidad: "SCRAPING", "SOCRATA", "SOCRATA_COMPLEMENTO" |

### Librerías utilizadas

- **pandas**: Manipulación de datos
- **geopandas**: Operaciones geoespaciales
- **shapely**: Reparación de geometrías (Polygon, MultiPolygon)
- **holidays**: Detección de festivos colombianos

### Ejecución

```bash
python scripts/03_process_silver_data.py
```

### Salidas

```
data/gold/base/
├── geo_gold.parquet        # Geometrías limpias
├── policia_gold.parquet    # Delitos estandarizados (con complementos Socrata)
├── socrata_gold.parquet    # Delitos Socrata procesados
├── poblacion_gold.parquet  # Población normalizada
└── divipola_gold.parquet   # Códigos DIVIPOLA
```

---

## 2. Integración Gold

**Script:** `scripts/03_generate_gold.py`

Combina todos los datasets Gold/base en un único dataset integrado con geometría.

### Proceso de integración

1. Carga de los 4 datasets base
2. Agregación de centros poblados por municipio
3. Join de delitos con geografía (por código DANE)
4. Join con datos de población (por código y año)
5. Agregación de estadísticas delictivas por municipio/año
6. **Agregación de conteos mensuales de días** (festivos, laborales, etc.)
7. Preservación de geometrías para visualización

### Librerías utilizadas

- **pandas**: Joins y agregaciones
- **geopandas**: Preservación de geometrías en joins

### Ejecución

```bash
python scripts/03_generate_gold.py
```

### Salida

```
data/gold/
└── gold_integrado.parquet  # Dataset unificado (~294 KB)
```

### Columnas principales del dataset integrado

| Columna | Descripción |
|---------|-------------|
| `codigo_municipio` | Código DANE del municipio |
| `municipio` | Nombre del municipio |
| `anio` | Año de los datos |
| `mes` | Mes de los datos |
| `geometry` | Geometría del municipio |
| `area_km2` | Área en kilómetros cuadrados |
| `poblacion_total` | Población total del municipio |
| `poblacion_menores` | Población menores de 12 años |
| `poblacion_adolescentes` | Población 12-17 años |
| `poblacion_adultos` | Población 18+ años |
| `n_centros_poblados` | Número de centros poblados |
| `HOMICIDIOS`, `HURTOS`, ... | Conteo por tipo de delito |
| `n_dias_semana` | Días lunes-viernes con delitos en el mes |
| `n_fines_de_semana` | Días sáb-dom con delitos en el mes |
| `n_festivos` | Días festivos con delitos en el mes |
| `n_dias_laborales` | Días hábiles con delitos en el mes |

---

## 3. Generación de Analytics

**Script:** `scripts/04_generate_analytics.py`

Calcula indicadores analíticos derivados del dataset integrado.

### Indicadores generados

**Tasas por 100.000 habitantes:**
- `tasa_homicidios`
- `tasa_hurtos`
- `tasa_lesiones`
- `tasa_violencia_intrafamiliar`
- `tasa_amenazas`
- `tasa_delitos_sexuales`
- `tasa_extorsion`
- `tasa_abigeato`

**Indicadores demográficos y espaciales:**
- `densidad_poblacional` — habitantes por km²
- `centros_por_km2` — centros poblados por km²
- `proporcion_menores` — % población menor de 12 años
- `proporcion_adolescentes` — % población 12-17 años
- `proporcion_adultos` — % población 18+ años

### Ejecución

```bash
python scripts/04_generate_analytics.py
```

### Salida

```
data/gold/analytics/
└── gold_analytics.parquet  # Dataset con indicadores (~300 KB)
```

---

## Resumen de salidas Gold

```
data/gold/
├── base/
│   ├── geo_gold.parquet        # Geometrías municipios
│   ├── policia_gold.parquet    # Delitos Policía + complementos
│   ├── socrata_gold.parquet    # Delitos Socrata procesados
│   ├── poblacion_gold.parquet  # Población normalizada
│   └── divipola_gold.parquet   # Códigos DIVIPOLA
├── analytics/
│   └── gold_analytics.parquet  # Con tasas e indicadores
└── gold_integrado.parquet      # Dataset principal
```

---

## Ejecución completa del pipeline Gold

Para ejecutar todo el proceso Gold en orden:

```bash
python scripts/03_process_silver_data.py
python scripts/03_generate_gold.py
python scripts/04_generate_analytics.py
```

---

## Siguiente paso

Con el dataset analítico listo, el siguiente paso es generar los datasets para Machine Learning. Consulta [04_model_data.md](04_model_data.md) para más detalles sobre los datasets de regresión y clasificación.
