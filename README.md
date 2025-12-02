# 📊 CrimeLab Santander
## Datos al Ecosistema - Reto Avanzado: Seguridad en Santander
### Propuesta de solución: https://crimelabsantander.streamlit.app/
### Video Pitch: https://www.youtube.com/watch?v=qliKMSQ1aTQ

Este repositorio contiene el desarrollo de la solución para el reto **"Datos al Ecosistema 2025"**, enfocado en el análisis y modelado de datos de seguridad y convivencia en el departamento de Santander.

| Sección | Descripción |
| :--- | :--- |
| [👥 Equipo](#equipo) | Miembros del equipo de desarrollo |
| [🎯 Objetivos generales](#objetivos-generales) | Visión general del plan de 6 etapas |
| [📂 Estructura General](#estructura-general) | Arquitectura de datos y modelo predictivo |
| [🚀 Estado actual](#estado-actual) | Detalle del progreso por componente |
| [📊 Dashboard](#dashboard) | Tablero interactivo de seguridad ciudadana |
| [⚡ Inicio rápido](#inicio-rapido) | Cómo ejecutar el proyecto |

<a id="equipo"></a>
## 👥 Equipo

Somos un equipo de **3 integrantes** comprometidos con el uso de datos para el impacto social:
- Alejandra Uribe Sierra 
- Shorly López Pérez
- Sergio Luis López Verbel

<a id="objetivos-generales"></a>
## 🎯 Objetivos generales

Para abordar el reto, hemos diseñado un plan de trabajo general compuesto por 6 etapas:

1.  ✅ **Recopilación de fuentes de datos.**
2.  ✅ **Creación de infraestructura de datos, limpieza y modelado.**
3.  ✅ **Diseño de Dashboard.**
4.  ✅ **Creación de modelos predictivos (descriptivos y ML).**
5.  ✅ **Desarrollo del Chatbot.**
6.  ✅ **Documentación, validación y entrega.**

<a id="estructura-general"></a>
## 📂 Estructura General

El proyecto sigue una arquitectura de medallón (Medallion Architecture) para el manejo de datos:

```
data/
├── bronze/          # Datos crudos tal como llegan de la fuente
├── silver/          # Datos limpios, validados y estandarizados
├── gold/            # Datos agregados y listos para reportes o IA
│   ├── base/        # Datos integrados principales
│   ├── analytics/   # Métricas y análisis calculados
│   ├── dashboard/   # Tablas optimizadas para el tablero
│   └── model/       # Datasets preparados para ML
└── models/          # Modelos entrenados (descriptivos y predictivos)
```

<a id="estado-actual"></a>
## 🚀 Estado actual del proyecto

### ✅ Ingesta de Datos (Capa Bronze)
Recopilación automática de datos desde múltiples fuentes oficiales:
- **Policía Nacional**: Estadísticas delictivas (Web Scraping y descargas)
- **Datos Abiertos (Socrata)**: Datasets gubernamentales
- **DANE**: Información geográfica y de división política (Divipola)
- **Plan Departamental de Desarrollo**: Metas y presupuestos

### ✅ Procesamiento y Limpieza (Capa Silver)
Estandarización, limpieza y estructuración de los datos para asegurar su calidad.

### ✅ Modelado y Enriquecimiento (Capa Gold)
Integración geoespacial (Policía + DANE) y agregación de datos para Dashboards y modelos.

### ✅ Modelado Predictivo
Modelos desarrollados en notebooks con dos enfoques:

| Tipo | Notebooks | Descripción |
|------|-----------|-------------|
| **Clasificación** | `05_classification_dominant_*.ipynb` | Predicción de delito/arma dominante por municipio-mes |
| **Clasificación** | `05_classification_event_*.ipynb` | Clasificación multiclase evento a evento |
| **Clasificación** | `05_classification_monthly_*.ipynb` | Riesgo mensual (Bajo/Medio/Alto) |
| **Regresión** | `05_regression_annual_*.ipynb` | Predicción de delitos anuales |
| **Clustering** | `05_clustering_geo.ipynb` | Agrupación geoespacial-delictiva de municipios |
| **Series de tiempo** | `05_eda_regression_*.ipynb` | Análisis y forecast temporal |

Cada modelo tiene versiones **descriptivas** (análisis) y **predictivas** (ML con XGBoost, Random Forest, etc.).

### ✅ Chatbot Comunitario
- Prototipo funcional en el Dashboard (pestaña "Chatbot comunitario")
- Agente basado en reglas que interpreta preguntas y filtra datos
- Incluye rutas de atención (línea 123, 155, Fiscalía)
- Pendiente: integración con LLM para respuestas más naturales

<a id="dashboard"></a>
## 📊 Dashboard de Seguridad Ciudadana

Tablero interactivo desarrollado en **Streamlit** con tres módulos:

### 1. Dashboard Descriptivo
- KPIs generales: casos totales, municipios con registros, población cubierta
- Comparación de casos vs metas departamentales (homicidios, hurtos, lesiones)
- Gráficos de distribución por municipio y tipo de delito
- Tendencia histórica con filtros interactivos

### 2. Chatbot Comunitario
- Agente de datos que interpreta preguntas en lenguaje natural
- Filtra por delito, municipio y año mencionados en la pregunta
- Calcula estadísticas y tendencias automáticamente
- Proporciona rutas de atención oficiales

### 3. Módulo Predictivo
- Explorador de datasets de modelado (clasificación, regresión, clustering)
- Documentación viva de cada dataset y su uso previsto
- Baseline histórico funcional (promedio de últimos 3 años)
- Preparado para integrar modelos ML entrenados

### Ejecutar el Dashboard

```bash
# Desde la raíz del proyecto
streamlit run app.py
```

El dashboard estará disponible en `http://localhost:8501`.

<a id="inicio-rapido"></a>
## ⚡ Inicio rápido

### Requisitos previos
- Python 3.11+
- Git

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/aluribes/Datos-al-Ecosistema.git
cd Datos-al-Ecosistema

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

> **macOS**: Si usas XGBoost, instala OpenMP: `brew install libomp`

### Ejecutar el pipeline completo

```bash
# 1. Configuración inicial
python scripts/00_setup.py

# 2. Ejecutar pipeline (Bronze → Silver → Gold → Model)
python run_pipeline.py

# 3. Iniciar dashboard
streamlit run app.py
```

Para más detalles, consulta la [documentación de instalación](docs/installation.md).

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [Installation](docs/installation.md) | Guía completa de instalación y ejecución |
| [Development](docs/development.md) | Guía para desarrolladores |
| [Pipeline: Bronze](docs/pipeline/01_bronze.md) | Capa de ingesta de datos |
| [Pipeline: Silver](docs/pipeline/02_silver.md) | Capa de limpieza |
| [Pipeline: Gold](docs/pipeline/03_gold.md) | Capa de modelado |
| [Pipeline: Model Data](docs/pipeline/04_model_data.md) | Datasets para ML |
| [Pipeline: Notebooks](docs/pipeline/05_notebooks.md) | Documentación de notebooks |
| [Dashboard Models](docs/dashboard_chatbot_models/) | Ayuda para modelos del chatbot |
