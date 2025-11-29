# Instalación

Guía para configurar el entorno de desarrollo del proyecto.

## Requisitos previos

- Python 3.12 o superior
- `pip` (incluido con Python)
- `git` para clonar el repositorio

## Pasos de instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/aluribes/Datos-al-Ecosistema.git
cd Datos-al-Ecosistema
```

### 2. Crear entorno virtual

Se recomienda usar un entorno virtual para aislar las dependencias del proyecto.

```bash
python3 -m venv .venv
```

Activar el entorno:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

> 💡 Sabrás que el entorno está activo cuando veas `(.venv)` al inicio de tu terminal.

### 3. Instalar dependencias

```bash
# Linux / macOS
source setup.sh

# Windows
setup
```

### 4. Dependencias del sistema (macOS)

En **macOS**, XGBoost requiere la librería OpenMP para funcionar. Si al importar `xgboost` obtienes un error como:

```
XGBoost Library (libxgboost.dylib) could not be loaded.
Likely causes: OpenMP runtime is not installed
```

Instala OpenMP con Homebrew:

```bash
brew install libomp
```

> 💡 Esto no es necesario en Linux (ya incluye `libgomp`) ni en Windows.

---

## Ejecución del Pipeline

El pipeline sigue una arquitectura medallion (Bronze → Silver → Gold → Model). Ejecutar los scripts en el orden indicado.

### Sección 00 — Setup

```bash
python scripts/00_setup.py
```

Crea la estructura de carpetas `data/bronze`, `data/silver`, `data/gold`.

### Sección 01 — Bronze (Extracción)

```bash
python scripts/01_extract_bronze.py
python scripts/01_scrape_policia_estadistica.py
python scripts/01_generate_polygon_santander.py
```

**Nota:** Debes descargar manualmente los archivos ZIP de población DANE en `data/bronze/poblacion_dane/`.

### Sección 02 — Silver (Limpieza)

```bash
python scripts/02_process_danegeo.py
python scripts/02_process_socrata.py
python scripts/02_socrata_bucaramanga_to_parquet.py
python scripts/02_process_policia.py
python scripts/02_process_policia_completo.py
python scripts/02_datos_poblacion_santander.py
python scripts/02_extract_metas.py
```

### Sección 03 — Gold (Integración)

```bash
python scripts/03_process_silver_data.py
python scripts/03_generate_gold.py
```

### Sección 04 — Model Data (Preparación ML)

```bash
# Analytics y Dashboard
python scripts/04_generate_analytics.py
python scripts/04_generate_dashboard_data.py

# Datasets para modelos
python scripts/04_generate_regression_monthly_dataset.py
python scripts/04_generate_regression_annual_dataset.py
python scripts/04_generate_regression_timeseries_dataset.py
python scripts/04_generate_classification_monthly_dataset.py
python scripts/04_generate_classification_event_dataset.py
python scripts/04_generate_classification_dominant_dataset.py
python scripts/04_generate_clustering_geo_dataset.py
```

---

## Estructura del proyecto

Una vez instalado, la estructura principal es:

```
Datos-al-Ecosistema/
├── data/                 # Datos (bronze, silver, gold)
│   ├── bronze/           # Datos crudos
│   ├── silver/           # Datos limpios
│   └── gold/             # Datos integrados + model datasets
├── scripts/              # Pipeline de procesamiento
├── notebooks/            # Notebooks de análisis y modelado
├── models/               # Modelos entrenados (.joblib, .json)
├── docs/                 # Documentación
│   ├── pipeline/         # Docs por sección (00-04)
│   └── dashboard_chatbot_models/  # Docs para chatbot
├── requirements.txt      # Dependencias
├── setup.bat             # Configuración en Windows
├── setup.sh              # Configuración en Linux o MacOS
└── app.py                # Aplicación Streamlit
```

## Siguiente paso

Consulta la documentación del pipeline en [`docs/pipeline/`](pipeline/) para entender el detalle de cada script.
