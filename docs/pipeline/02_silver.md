# Capa Silver — Limpieza y Transformación

La capa Silver contiene los datos limpios y estandarizados, listos para ser integrados en la capa Gold.

## Scripts de procesamiento

| Script | Entrada | Salida | Orden |
|--------|---------|--------|-------|
| `02_process_danegeo.py` | Bronze: DIVIPOLA, GeoJSON | Silver: geografía y códigos | 1 |
| `02_process_socrata.py` | Bronze: JSONs Socrata (7 delitos) | Silver: consolidado delitos | 2 |
| `02_process_policia.py` | Bronze: Excel Policía | Silver: policia_santander | 3 |
| `02_process_policia_completo.py` | Bronze: Excel Policía | Silver: policia_completo | 4 |
| `02_datos_poblacion_santander.py` | Bronze: TerriData ZIPs | Silver: población | 5 |
| `02_extract_metas.py` | Bronze: Excel metas | Silver: metas parquet | 6 |
| `02_socrata_bucaramanga_to_parquet.py` | Bronze: JSONs Bucaramanga | Silver: Bucaramanga + informáticos | 7 |

> **Nota sobre orden**: Los scripts 1-5 son el flujo principal. Los scripts 6-7 son opcionales/complementarios para datos adicionales.

---

## 1. Procesamiento DANE y Geografía

**Script:** `scripts/02_process_danegeo.py`

Procesa los datos geográficos: códigos DIVIPOLA y geometrías de municipios de Santander.

### Transformaciones aplicadas

- Lectura del archivo DIVIPOLA (Excel .xls)
- Filtrado por departamento de Santander
- Normalización de nombres (mayúsculas, sin acentos)
- Cálculo de área en km² para cada municipio
- Conversión de geometrías a formato estándar

### Librerías utilizadas

- **pandas**: Manipulación de datos tabulares
- **geopandas**: Operaciones geoespaciales
- **unidecode**: Eliminación de acentos en nombres

### Ejecución

```bash
python scripts/02_process_danegeo.py
```

### Salidas

```
data/silver/dane_geo/
├── divipola_silver.parquet      # Códigos municipios Santander
├── geografia_silver.parquet     # Geometrías con área calculada
└── geografia_silver.geojson     # Geometrías en formato GeoJSON
```

---

## 2. Procesamiento Socrata (Consolidado Delitos)

**Script:** `scripts/02_process_socrata.py`

Consolida los 7 datasets principales de delitos de Socrata en un único archivo con esquema estandarizado.

### Datasets procesados

| Dataset Bronze | Tipo de Delito |
|---------------|----------------|
| `homicidios.json` | HOMICIDIOS |
| `extorsion.json` | EXTORSION |
| `hurto_personas.json` | HURTO_PERSONAS |
| `lesiones.json` | LESIONES |
| `amenazas.json` | AMENAZAS |
| `delitos_sexuales.json` | DELITOS_SEXUALES |
| `violencia_intrafamiliar.json` | VIOLENCIA_INTRAFAMILIAR |

### Esquema Silver normalizado

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `tipo_delito` | str | Nombre del delito basado en archivo origen |
| `fecha_hecho` | datetime | Fecha del evento |
| `cod_muni` | str | Código DANE municipio (5 dígitos) |
| `municipio` | str | Nombre del municipio (mayúsculas) |
| `departamento` | str | Siempre "SANTANDER" |
| `genero` | str | Género de la víctima o "NO REPORTADO" |
| `arma_medio` | str | Arma/medio utilizado o "NO REPORTADO" |
| `cantidad` | int | Cantidad de casos |

### Ejecución

```bash
python scripts/02_process_socrata.py
```

### Salida

```
data/silver/delitos/
└── consolidado_delitos.parquet  # Delitos unificados de Socrata
```

---

## 3. Procesamiento Policía Nacional (Santander)

**Script:** `scripts/02_process_policia.py`

Consolida los ~265 archivos Excel de estadísticas delictivas en un único dataset estructurado, **filtrado solo para Santander**.

### Transformaciones aplicadas

- Detección automática de fila de encabezado en cada Excel
- Estandarización de nombres de columnas
- Filtrado por departamento de Santander
- Consolidación de todos los años (2010-2025)
- Limpieza de valores nulos y duplicados
- Normalización de tipos de delito
- Agrega `codigo_municipio` normalizado (5 dígitos)

### Librerías utilizadas

- **pandas**: Lectura de Excel y manipulación
- **openpyxl** / **xlrd**: Motores de lectura Excel

### Ejecución

```bash
python scripts/02_process_policia.py
```

### Salida

```
data/silver/policia_scraping/
└── policia_santander.parquet    # Delitos Santander consolidados
```

---

## 4. Procesamiento Policía Nacional (Colombia Completo)

**Script:** `scripts/02_process_policia_completo.py`

Similar al script anterior pero **sin filtrar por departamento**, genera un dataset con todos los departamentos de Colombia.

### Ejecución

```bash
python scripts/02_process_policia_completo.py
```

### Salida

```
data/silver/policia_scraping/
└── policia_completo.parquet     # Delitos Colombia consolidados
```

---

## 5. Procesamiento Población

**Script:** `scripts/02_datos_poblacion_santander.py`

Procesa datos de población por municipio, edad y año desde TerriData del DNP.

### Archivos de entrada requeridos

| Archivo | Contenido | Período |
|---------|-----------|---------|
| `TerriData_Pob_2005.zip` | TerriData_Pob_2005.txt | 2005-2017 |
| `TerriData_Pob_2018.zip` | TerriData_Pob_2018.txt | 2018-2035 |

> ⚠️ Estos archivos deben estar en `data/bronze/poblacion_dane/`

### Transformaciones aplicadas

- Filtrado por departamento de Santander
- Clasificación de grupos de edad (MENORES, ADOLESCENTES, ADULTOS)
- Agregación por municipio, año, género y grupo de edad
- Estandarización de género (MASCULINO/FEMENINO)

### Librerías utilizadas

- **pandas**: Manipulación de datos
- **zipfile**: Lectura de archivos ZIP (biblioteca estándar)

### Ejecución

```bash
python scripts/02_datos_poblacion_santander.py
```

### Salida

```
data/silver/poblacion/
└── poblacion_santander.parquet  # Población por municipio/año/género/edad
```

---

## 6. Extracción Metas Plan de Desarrollo (Opcional)

**Script:** `scripts/02_extract_metas.py`

Convierte las tablas de metas del Plan de Desarrollo desde Excel a Parquet sin transformar la estructura.

### Ejecución

```bash
python scripts/02_extract_metas.py
```

### Salidas

```
data/silver/metas/
├── mandatos.parquet
└── metas.parquet
```

---

## 7. Procesamiento Bucaramanga y Delitos Informáticos (Opcional)

**Script:** `scripts/02_socrata_bucaramanga_to_parquet.py`

Procesa datasets específicos de Bucaramanga y delitos informáticos con limpieza especializada.

### Transformaciones aplicadas

- Unificación de datasets de Bucaramanga (40 delitos + 150 información delictiva)
- Normalización de fechas, coordenadas y columnas
- Deducción de campos faltantes (fecha a partir de año/mes/día)
- Extracción de artículos desde descripción de conducta
- Eliminación de duplicados

### Ejecución

```bash
python scripts/02_socrata_bucaramanga_to_parquet.py
```

### Salidas

```
data/silver/socrata_api/
├── delitos_bucaramanga.parquet    # Bucaramanga unificado y limpio
└── delitos_informaticos.parquet   # Delitos informáticos limpio
```

---

## Resumen de salidas Silver

```
data/silver/
├── dane_geo/
│   ├── divipola_silver.parquet      # Códigos DIVIPOLA Santander
│   ├── geografia_silver.parquet     # Geometrías municipios
│   └── geografia_silver.geojson     # Geometrías en GeoJSON
├── delitos/
│   └── consolidado_delitos.parquet  # Delitos Socrata consolidados
├── policia_scraping/
│   ├── policia_santander.parquet    # Delitos Policía (Santander)
│   └── policia_completo.parquet     # Delitos Policía (Colombia)
├── poblacion/
│   └── poblacion_santander.parquet  # Población por municipio
├── metas/                           # (Opcional)
│   ├── mandatos.parquet
│   └── metas.parquet
└── socrata_api/                     # (Opcional)
    ├── delitos_bucaramanga.parquet
    └── delitos_informaticos.parquet
```

---

## Siguiente paso

Con los datos limpios, continúa con la [Capa Gold](03_gold.md) para integrar todas las fuentes en un dataset unificado.
