# Capa Bronze — Extracción de Datos Crudos

La capa Bronze contiene los datos en su formato original, tal como fueron extraídos de las fuentes externas.

## Prerequisito: Estructura de carpetas

Antes de ejecutar cualquier script de extracción, asegúrate de que exista la estructura de carpetas:

```bash
python scripts/00_setup.py
```

> ⚠️ **Nota**: El repositorio ya incluye las carpetas `data/bronze`, `data/silver` y `data/gold`. Solo es necesario ejecutar este script si clonaste el repositorio por primera vez y las carpetas están vacías o no existen.

---

## Scripts de extracción

| Script | Fuente | Salida |
|--------|--------|--------|
| `01_extract_bronze.py` | Socrata API, DANE | JSON, Excel |
| `01_generate_polygon_santander.py` | GitHub (GeoJSON Colombia) | GeoJSON |
| `01_scrape_policia_estadistica.py` | Policía Nacional | Excel (.xlsx) |

---

## 1. Extracción Socrata y DANE

**Script:** `scripts/01_extract_bronze.py`

Descarga datasets desde [datos.gov.co](https://www.datos.gov.co/) usando la API de Socrata, además del archivo DIVIPOLA desde el DANE.

### Datasets descargados

| Dataset | ID Socrata | Descripción |
|---------|------------|-------------|
| `delitos_sexuales` | fpe5-yrmw | Delitos sexuales a nivel nacional |
| `violencia_intrafamiliar` | vuyt-mqpw | Casos de violencia intrafamiliar |
| `hurto_modalidades` | d4fr-sbn2 | Modalidades de hurto |
| `bucaramanga_delictiva_150` | x46e-abhz | Actividad delictiva Bucaramanga |
| `bucaramanga_delitos_40` | 75fz-q98y | Delitos Bucaramanga |
| `delitos_informaticos` | 4v6r-wu98 | Delitos informáticos |

### Librerías utilizadas

- **sodapy**: Cliente Python para la API de Socrata
- **requests**: Descarga de archivos HTTP
- **pandas**: Conversión a JSON

### Ejecución

```bash
python scripts/01_extract_bronze.py
```

### Salidas

```
data/bronze/
├── socrata_api/
│   ├── delitos_sexuales.json
│   ├── violencia_intrafamiliar.json
│   ├── hurto_modalidades.json
│   ├── bucaramanga_delictiva_150.json
│   ├── bucaramanga_delitos_40.json
│   └── delitos_informaticos.json
└── dane_geo/
    └── divipola_2010.xls
```

---

## 2. Polígonos de Santander

**Script:** `scripts/01_generate_polygon_santander.py`

Descarga el GeoJSON de municipios de Colombia y filtra únicamente los del departamento de Santander (código DANE: 68).

### Fuente

- Repositorio GitHub: [caticoa3/colombia_mapa](https://github.com/caticoa3/colombia_mapa)
- Archivo: `co_2018_MGN_MPIO_POLITICO.geojson`

### Librerías utilizadas

- **requests**: Descarga del archivo
- **geopandas**: Lectura y filtrado de geometrías

### Ejecución

```bash
python scripts/01_generate_polygon_santander.py
```

### Salida

```
data/bronze/dane_geo/
└── santander_municipios.geojson    # 87 municipios
```

---

## 3. Scraping Policía Nacional

**Script:** `scripts/01_scrape_policia_estadistica.py`

Extrae archivos Excel de estadísticas delictivas desde el portal de la [Policía Nacional](https://www.policia.gov.co/estadistica-delictiva).

### Datos extraídos

- **Período**: 2010 - 2024
- **Delitos**: Homicidios, hurtos, lesiones, abigeato, amenazas, extorsión, entre otros
- **Formato**: Archivos Excel (.xlsx) por año y tipo de delito

### Librerías utilizadas

- **requests**: Peticiones HTTP
- **BeautifulSoup**: Parsing de HTML para encontrar enlaces
- **unicodedata**: Normalización de nombres de archivos

### Ejecución

```bash
python scripts/01_scrape_policia_estadistica.py
```

> ⚠️ **Nota**: Este proceso puede tomar varios minutos debido a la cantidad de archivos y tiempos de espera entre peticiones para evitar saturar el servidor.

### Salida

```
data/bronze/policia_scraping/
├── 2010_Abigeato_abigeato_2010_0.xlsx
├── 2010_Amenazas_amenazas_2010.xlsx
├── 2010_Homicidios_Homicidio_Intencional_2010.xlsx
├── ...
└── 2024_Violencia_Intrafamiliar_....xlsx
```

Total: ~241 archivos Excel

---

## Resumen de salidas Bronze

```
data/bronze/
├── dane_geo/
│   ├── divipola_2010.xls           # Códigos DIVIPOLA
│   └── santander_municipios.geojson # Geometrías municipios
├── policia_scraping/
│   └── *.xlsx                       # 241 archivos de estadísticas a NOV 2025
└── socrata_api/
    └── *.json                       # 6 datasets de datos.gov.co
```

---

## Siguiente paso

Una vez extraídos los datos crudos, continúa con la [Capa Silver](02_silver.md) para limpiar y transformar los datos.
