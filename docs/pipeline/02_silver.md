# Capa Silver — Limpieza y Transformación

La capa Silver contiene los datos limpios y estandarizados, listos para ser integrados en la capa Gold.

## Scripts de procesamiento

| Script | Entrada | Salida |
|--------|---------|--------|
| `02_process_danegeo.py` | Bronze: DIVIPOLA, GeoJSON | Silver: geografía y códigos |
| `02_process_policia.py` | Bronze: Excel Policía | Silver: delitos consolidados |
| `02_datos_poblacion_santander.py` | Bronze: TerriData | Silver: población por municipio |

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
└── geografia_silver.parquet     # Geometrías con área calculada
```

---

## 2. Procesamiento Policía Nacional

**Script:** `scripts/02_process_policia.py`

Consolida los ~241 archivos Excel de estadísticas delictivas en un único dataset estructurado.

### Transformaciones aplicadas

- Detección automática de fila de encabezado en cada Excel
- Estandarización de nombres de columnas
- Filtrado por departamento de Santander
- Consolidación de todos los años (2010-2024)
- Limpieza de valores nulos y duplicados
- Normalización de tipos de delito

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
└── policia_santander.parquet    # Delitos consolidados (~3.2 MB)
```

---

## 3. Procesamiento Población

**Script:** `scripts/02_datos_poblacion_santander.py`

Procesa datos de población por municipio, edad y año desde TerriData del DNP.

### ⚠️ Archivo de entrada no incluido en el repositorio

El archivo de entrada `TerriData_Dim2.txt` (~100+ MB) **no está incluido en el repositorio** debido a las limitaciones de tamaño de GitHub.

**Sin embargo**, la salida procesada (`poblacion_santander.parquet`) **sí está incluida**, por lo que no es necesario ejecutar este script para reproducir el pipeline.

### Cómo obtener el archivo fuente (opcional)

1. Visitar [TerriData - DNP](https://terridata.dnp.gov.co/)
2. Descargar la dimensión de población
3. Guardar como `data/bronze/poblacion_2018/TerriData_Dim2.txt`

### Transformaciones aplicadas

- Filtrado por departamento de Santander
- Clasificación de grupos de edad (menores, adolescentes, adultos)
- Agregación por municipio y año
- Cálculo de población total por grupo

### Librerías utilizadas

- **pandas**: Manipulación de datos
- **re**: Expresiones regulares para extraer edades

### Ejecución

```bash
python scripts/02_datos_poblacion_santander.py
```

> ⚠️ Requiere el archivo `TerriData_Dim2.txt` en `data/bronze/poblacion_2018/`

### Salida

```
data/silver/poblacion/
└── poblacion_santander.parquet  # Población por municipio/año (~36 KB)
```

---

## Resumen de salidas Silver

```
data/silver/
├── dane_geo/
│   ├── divipola_silver.parquet     # Códigos DIVIPOLA
│   └── geografia_silver.parquet    # Geometrías municipios
├── policia_scraping/
│   └── policia_santander.parquet   # Delitos consolidados
└── poblacion/
    └── poblacion_santander.parquet # Población por municipio ✔ (incluido)
```

---

## Siguiente paso

Con los datos limpios, continúa con la [Capa Gold](03_gold.md) para integrar todas las fuentes en un dataset unificado.
