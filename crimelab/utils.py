import streamlit as st
import json
import os
import joblib 
from PIL import Image
import numpy as np
# ============================
# CONFIGURACIÓN DE RUTAS
# ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

def get_file_path(base_dir, *relative_path_components):
    """Genera una ruta normalizada para cualquier sistema operativo."""
    return os.path.normpath(os.path.join(base_dir, *relative_path_components))

# ============================
# FUNCIONES DE CARGA DE MODELOS PREDICTIVOS
# ============================

@st.cache_resource(show_spinner="Cargando modelos predictivos...") 
def load_predictive_models():
    """Carga los modelos de predicción (joblib) y sus componentes para el modelo Dominante."""
    modelos = {}
    try:
        # Rutas de Modelos Predictivos DOMINANT
        model_path = get_file_path(BASE_DIR, ".." ,"models", "predictivos", "classification_dominant", "xgb_multioutput.joblib")
        le_delito_path = get_file_path(BASE_DIR, ".." ,"models", "predictivos", "classification_dominant", "label_encoder_delito.joblib")
        le_arma_path = get_file_path(BASE_DIR, ".." ,"models", "predictivos", "classification_dominant", "label_encoder_arma.joblib")
        scaler_path = get_file_path(BASE_DIR, ".." ,"models", "predictivos", "classification_dominant", "scaler.joblib")
        
        modelos["model"] = joblib.load(model_path)
        modelos["le_delito"] = joblib.load(le_delito_path)
        modelos["le_arma"] = joblib.load(le_arma_path)
        modelos["scaler"] = joblib.load(scaler_path)
        
        return modelos
    except FileNotFoundError as e:
        st.error(f"Error al cargar archivos .joblib (Dominante): Asegúrese de que la ruta sea correcta. Detalles: {e}")
        return None
    except Exception as e:
        st.error(f"Error crítico al cargar componentes del modelo Dominante. Detalles: {e}")
        return None


# ============================
# FUNCIONES DE CARGA DE DATOS DESCRIPTIVOS Y GEOGRÁFICOS (DUAL)
# ============================

@st.cache_data(show_spinner="Cargando datos descriptivos y geográficos...")
def load_descriptive_data():
    """Carga todos los archivos JSON, GeoJSON y los mapeos necesarios."""
    data_dominant, data_event = {}, {}
    geojson_data = {}
    municipio_name_map = {}
    
    # Rutas base para los modelos
    dominant_dir = get_file_path(BASE_DIR, ".." ,"models", "descriptivo", "classification_dominant")
    event_dir = get_file_path(BASE_DIR, ".." ,"models", "descriptivo", "classification_event")
    geojson_path = get_file_path(BASE_DIR, ".." ,"data", "silver", "dane_geo", "geografia_silver.geojson")
    
    # Lista de archivos para carga (Nombre interno: Ruta relativa)
    files_to_load = {
        # DOMINANT
        "stats_dom": get_file_path(dominant_dir, "estadisticas_generales.json"),
        "mun_resumen_dom": get_file_path(dominant_dir, "municipios_resumen.json"),
        "tendencias_dom": get_file_path(dominant_dir, "tendencias_anuales.json"),
        # EVENT
        "resumen_event": get_file_path(event_dir, "resumen_general.json"),
        "distribucion_delitos_event": get_file_path(event_dir, "distribucion_delitos.json"),
        "distribucion_perfiles_event": get_file_path(event_dir, "distribucion_perfiles.json"),
        "temporal_event": get_file_path(event_dir, "analisis_temporal.json"),
        "demografico_event": get_file_path(event_dir, "analisis_demografico.json"),
        "geografico_event": get_file_path(event_dir, "analisis_geografico.json"),
        "cruces_delito_perfil_event": get_file_path(event_dir, "cruces_delito_perfil.json"),
        "top_combinaciones_event": get_file_path(event_dir, "top_combinaciones.json"),
        "respuestas_chatbot_event": get_file_path(event_dir, "respuestas_chatbot.json"),
    }
    
    try:
        # Cargar GeoJSON primero
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        # Cargar todos los JSONs descriptivos
        for key, path in files_to_load.items():
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
                
                # Clasificar en los diccionarios de retorno
                if key.endswith("_dom"):
                    data_dominant[key.replace("_dom", "")] = content
                elif key.endswith("_event"):
                    # Esta parte es la que genera la clave corta (ej: "resumen")
                    data_event[key.replace("_event", "")] = content

        # Procesamiento de GeoJSON (Común)
        for feature in geojson_data.get("features", []):
            codigo = str(feature["properties"].get("codigo_municipio"))
            nombre = feature["properties"].get("municipio")
            if codigo and nombre:
                municipio_name_map[codigo] = nombre.upper()

        # Retorna 4 elementos: los dos dicts de datos, el geojson y el mapa de nombres
        return data_dominant, data_event, geojson_data, municipio_name_map

    except FileNotFoundError as e:
        # Se detiene si falta algún archivo
        st.error(f"Error al cargar archivos descriptivos/geográficos: Revise las rutas. Detalles: {e}")
        st.stop()
    except Exception as e:
        # Manejo de cualquier otro error (incluyendo el de codificación)
        st.error(f"Error inesperado durante la carga de datos descriptivos. Detalles: {e}")
        # En caso de error, el control debe detener la ejecución aquí.
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