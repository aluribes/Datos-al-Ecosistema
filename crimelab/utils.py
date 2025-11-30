import streamlit as st
import json
import os
import joblib 
from PIL import Image

# ============================
# CONFIGURACIÓN DE RUTAS
# ============================
# BASE_DIR siempre apunta al directorio donde reside utils.py 
# (Asumimos: La carpeta 'crimelab' o la raíz del proyecto)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

# Función de construcción de rutas robusta y multiplataforma
def get_file_path(base_dir, *relative_path_components):
    """Genera una ruta normalizada para cualquier sistema operativo."""
    return os.path.normpath(os.path.join(base_dir, *relative_path_components))

# ============================
# FUNCIONES DE CARGA DE MODELOS
# ============================

@st.cache_resource(show_spinner="Cargando modelos predictivos...") 
def load_predictive_models():
    """Carga los modelos de predicción (joblib) y sus componentes."""
    modelos = {}
    try:
        # Rutas de Modelos Predictivos
        model_path = get_file_path(BASE_DIR, ".." ,"models", "predictivos", "classification_dominant", "xgb_multioutput.joblib")
        le_delito_path = get_file_path(BASE_DIR, ".." ,"models", "predictivos", "classification_dominant", "label_encoder_delito.joblib")
        le_arma_path = get_file_path(BASE_DIR, "..", "models", "predictivos", "classification_dominant", "label_encoder_arma.joblib")
        scaler_path = get_file_path(BASE_DIR, "..", "models", "predictivos", "classification_dominant", "scaler.joblib")

        # st.info(f"DEBUG: Intentando cargar modelo desde: {model_path}") # <-- Úsalo para depurar la ruta
        
        modelos["model"] = joblib.load(model_path)
        modelos["le_delito"] = joblib.load(le_delito_path)
        modelos["le_arma"] = joblib.load(le_arma_path)
        modelos["scaler"] = joblib.load(scaler_path)
        
        return modelos
    except FileNotFoundError as e:
        # Aquí se captura el error y se detiene la aplicación con el mensaje
        st.error(f"Error al cargar archivos .joblib: Asegúrese de que la ruta sea correcta. Detalles: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Error crítico al cargar componentes del modelo. Detalles: {e}")
        st.stop()


# ============================
# FUNCIONES DE CARGA DE DATOS DESCRIPTIVOS Y GEOGRÁFICOS
# ============================

@st.cache_data(show_spinner="Cargando datos descriptivos y geográficos...")
def load_descriptive_data():
    """Carga todos los archivos JSON y GeoJSON descriptivos."""
    stats, mun_resumen, geojson_data, tendencias = {}, {}, {}, {}
    municipio_name_map = {}
    
    try:
        # Rutas de Datos Descriptivos y Geoespaciales
        stats_path = get_file_path(BASE_DIR, ".." ,"models", "descriptivo", "classification_dominant", "estadisticas_generales.json")
        mun_resumen_path = get_file_path(BASE_DIR, ".." ,"models", "descriptivo", "classification_dominant", "municipios_resumen.json")
        tendencias_path = get_file_path(BASE_DIR, ".." ,"models", "descriptivo", "classification_dominant", "tendencias_anuales.json")
        geojson_path = get_file_path(BASE_DIR, "..", "data", "silver", "dane_geo", "geografia_silver.geojson")

        # 1. Carga de JSONs Descriptivos
        with open(stats_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
        with open(mun_resumen_path, "r", encoding="utf-8") as f:
            mun_resumen = json.load(f)
        with open(tendencias_path, "r", encoding="utf-8") as f:
            tendencias = json.load(f)
        
        # 2. Carga de GeoJSON 
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        # 3. Crear mapeo de nombres (La lógica ya era correcta)
        for feature in geojson_data.get("features", []):
            codigo = str(feature["properties"].get("codigo_municipio"))
            nombre = feature["properties"].get("municipio")
            if codigo and nombre:
                nombre_upper = nombre.upper()
                municipio_name_map[codigo] = nombre_upper
                if codigo in mun_resumen and 'nombre' not in mun_resumen[codigo]:
                    mun_resumen[codigo]['nombre'] = nombre_upper
        
        return stats, mun_resumen, tendencias, geojson_data, municipio_name_map

    except FileNotFoundError as e:
        st.error(f"Error al cargar archivos descriptivos/geográficos: Revise las rutas. Detalles: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Error inesperado durante la carga de datos descriptivos. Detalles: {e}")
        st.stop()


# ============================
# FUNCIONES DE ESTILOS (Inyección CSS desde archivo)
# ============================

def inject_styles():
    """Lee el contenido del archivo CSS y lo inyecta en la página de Streamlit."""
    
    # 1. Usamos get_file_path para encontrar el archivo de forma robusta
    css_file_path = get_file_path(BASE_DIR, "assets", "styles.css")
    
    if os.path.exists(css_file_path):
        try:
            with open(css_file_path, "r", encoding="utf-8") as f:
                css = f.read()
            
            # 2. Inyectamos el CSS con la etiqueta <style>
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error al inyectar estilos desde assets/styles.css: {e}")
    else:
        # Esto ayuda a diagnosticar si el archivo no está en la ruta correcta
        st.warning(f"No se encontró el archivo de estilos en: {css_file_path}")

# ============================
# FUNCIONES DE UI / MENÚ
# ============================

def draw_sidebar_menu():
    """Dibuja el menú lateral de navegación en todas las páginas."""
    
    # --- 1. Logo ---
    # La llamada a get_file_path ahora funciona correctamente.
    logo_path = get_file_path(BASE_DIR, "assets", "logo_crimelab.png")

    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            st.sidebar.markdown("<div class='logo-container'>", unsafe_allow_html=True)
            st.sidebar.image(logo, use_container_width=False, width=150)
            st.sidebar.markdown("</div>", unsafe_allow_html=True)
        except Exception:
            st.sidebar.write("⚠️ Error al cargar el logo. Revisa el archivo 'assets/logo_crimelab.png'.")
    else:
        st.sidebar.write("⚠️ Agrega tu logo en assets/logo_crimelab.png")

    # --- 2. Links ---
    st.sidebar.markdown("## Navegación")

    def sidebar_link(emoji, label, page):
        st.sidebar.markdown(
            f"""
            <a href="/{page}" target="_self" style="text-decoration:none; font-size:17px;">
                {emoji} &nbsp; <span style="color:white;">{label}</span>
            </a>
            """,
            unsafe_allow_html=True
        )

    # Nota: Los links deben apuntar a los nombres de archivo sin la extensión .py
    sidebar_link("🏠", "Inicio", "")
    sidebar_link(" 📊 ", "Visor Analítico", "1_Visor_Analitico")
    sidebar_link(" 🤖 ", "ALBA", "2_Chatbot")
    sidebar_link("📁", "Datos", "3_Datos")
    sidebar_link("ℹ️", "Información", "4_Información")