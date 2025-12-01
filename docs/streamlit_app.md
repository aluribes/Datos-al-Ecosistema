# Streamlit App: CrimeLab

## Descripción

CrimeLab es la aplicación web interactiva del ecosistema de datos de seguridad ciudadana para Santander. Proporciona visualizaciones, análisis descriptivos, modelos predictivos y un asistente conversacional para explorar la información de criminalidad del departamento.

## Estructura de la Aplicación

```
crimelab/
├── app.py                 # Entrypoint principal (st.Page + st.navigation)
├── assets/
│   ├── logo_crimelab.png  # Logo de la aplicación
│   └── styles.css         # Estilos CSS personalizados
└── pages/
    ├── home.py            # Página de inicio (/)
    ├── dashboard.py       # Visor analítico (/dashboard)
    ├── chatbot.py         # Asistente ALBA (/chatbot)
    └── about.py           # Información del proyecto (/about)
```

## Ejecución

```bash
cd crimelab
streamlit run app.py
```

O desde la raíz del proyecto:

```bash
streamlit run crimelab/app.py
```

La aplicación estará disponible en `http://localhost:8501`

## Rutas y Navegación

| Ruta | Página | Descripción |
|------|--------|-------------|
| `/` | Inicio | Presentación del proyecto y navegación principal |
| `/dashboard` | Visor Analítico | Mapas, gráficos y análisis de criminalidad |
| `/chatbot` | ALBA | Asistente conversacional con IA |
| `/about` | Información | Documentación y arquitectura del proyecto |

## Páginas

### 🏠 Inicio (`pages/home.py`)

Página de bienvenida que presenta:
- Descripción general del proyecto CrimeLab
- Objetivos y alcance del ecosistema
- Navegación a las secciones principales

### 📊 Visor Analítico (`pages/dashboard.py`)

Dashboard interactivo con dos pestañas principales:

**Históricos y Descriptivos:**
- Indicadores globales (total eventos, período, municipios)
- Análisis demográfico por grupo etario
- Distribución de delitos y perfiles
- Mapa coroplético de clasificación de riesgo municipal
- Tendencia anual histórica y proyectada
- Ranking de criminalidad municipal

**Proyecciones:**
- Selector de modelo predictivo
- Controles de predicción (municipio, mes, año)
- Resultados de predicción (delito y arma dominante)

**Datos utilizados:**
- `models/descriptivo/classification_dominant/` - Estadísticas generales, resumen municipal, tendencias
- `models/descriptivo/classification_event/` - Análisis de eventos, perfiles, demografía
- `models/predictivos/classification_dominant/` - Modelos XGBoost, encoders, scalers
- `data/silver/dane_geo/geografia_silver.geojson` - Geometrías municipales

### 🤖 ALBA Chatbot (`pages/chatbot.py`)

Asistente conversacional inteligente potenciado por **Gemini 2.0 Flash Lite**:

- Responde preguntas sobre seguridad ciudadana en Santander
- Proporciona estadísticas y datos descriptivos
- Información específica por municipio
- Contexto histórico y tendencias

**Configuración:**
- API Key de Google en archivo `.env`: `GOOGLE_API_KEY="..."`
- Modelo: `gemini-2.0-flash-lite`

**Características:**
- Historial de conversación persistente en sesión
- Preguntas sugeridas en el sidebar
- Contexto enriquecido con datos del ecosistema

### ℹ️ Información (`pages/about.py`)

Documentación del proyecto:
- Arquitectura Medallion (Bronze → Silver → Gold)
- Metodología y fuentes de datos
- Descripción de modelos analíticos

## Dependencias Específicas

```
# --- Web application ---
streamlit==1.51.0

# --- AI / LLM ---
google-generativeai==0.8.5
python-dotenv==1.2.1

# --- Visualización ---
plotly==6.5.0
Pillow==12.0.0

# --- Tablero ---
folium==0.15.1
streamlit-folium==0.18.0
branca==0.6.0
```

## Configuración de Entorno

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
GOOGLE_API_KEY="tu-api-key-de-google"
```

### Streamlit Cloud

Para desplegar en Streamlit Cloud:

1. Subir repositorio a GitHub
2. Acceder a [share.streamlit.io](https://share.streamlit.io)
3. Configurar:
   - **Repository:** `usuario/Datos-al-Ecosistema`
   - **Branch:** `main`
   - **Main file path:** `crimelab/app.py`
4. En **Secrets**, agregar:
   ```toml
   GOOGLE_API_KEY = "tu-api-key-de-google"
   ```

## Arquitectura de Navegación

La aplicación utiliza `st.Page` y `st.navigation` (Streamlit 1.36+) para navegación multi-página con URLs personalizadas:

```python
# app.py
home_page = st.Page(home_render, title="Inicio", url_path="", default=True)
dashboard_page = st.Page(dashboard_render, title="Visor Analítico", url_path="dashboard")
chatbot_page = st.Page(chatbot_render, title="ALBA Chatbot", url_path="chatbot")
about_page = st.Page(about_render, title="Información", url_path="about")

pg = st.navigation({
    "Principal": [home_page],
    "Herramientas": [dashboard_page, chatbot_page],
    "Documentación": [about_page],
})
pg.run()
```

## Notas de Desarrollo

- Cada página exporta una función `render()` que es invocada por el router
- Los estilos CSS se inyectan globalmente desde `app.py`
- El logo se muestra en el sidebar de todas las páginas
- Los datos se cargan con `@st.cache_data` y `@st.cache_resource` para optimizar rendimiento
- El estado de la conversación del chatbot se mantiene en `st.session_state`

## Siguiente Paso

Para modificar o extender la aplicación:
- Agregar nuevas páginas en `pages/`
- Registrarlas en `app.py` con `st.Page`
- Ver documentación de Streamlit: [Multipage Apps](https://docs.streamlit.io/develop/concepts/multipage-apps)
