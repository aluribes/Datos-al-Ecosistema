import streamlit as st
import json
import os
import pandas as pd
import numpy as np
import joblib 
import datetime

# ============================
# CONFIGURACIÓN DE RUTAS
# ============================
# Directorio base: Asumimos que los modelos, assets, etc., están en el directorio raíz del proyecto.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_file_path(base, *relative_path_components):
    """
    Genera una ruta normalizada y segura. 
    Asegura que la ruta es correcta, asumiendo que el script de utilidad 
    está en la raíz del proyecto o sabe dónde están sus datos.
    """
    return os.path.normpath(os.path.join(base, *relative_path_components))

# ============================
# FUNCIONES DE CARGA (Usadas en todos los scripts)
# ============================

@st.cache_resource(show_spinner="Cargando modelos predictivos...") 
def load_predictive_models():
    """Carga los modelos de predicción (joblib) y sus componentes."""
    modelos = {}
    try:
        modelos["model"] = joblib.load(get_file_path(BASE_DIR, "models", "predictivos", "classification_dominant", "xgb_multioutput.joblib"))
        modelos["le_delito"] = joblib.load(get_file_path(BASE_DIR, "models", "predictivos", "classification_dominant", "label_encoder_delito.joblib"))
        modelos["le_arma"] = joblib.load(get_file_path(BASE_DIR, "models", "predictivos", "classification_dominant", "label_encoder_arma.joblib"))
        modelos["scaler"] = joblib.load(get_file_path(BASE_DIR, "models", "predictivos", "classification_dominant", "scaler.joblib"))
        
        return modelos
    except FileNotFoundError as e:
        st.error(f"Error al cargar archivos .joblib: Asegúrese de que la carpeta 'models/predictivos/classification_dominant' existe y contiene todos los archivos necesarios. Detalles: {e}")
        return None
    except Exception as e:
        st.error(f"Error crítico al cargar componentes del modelo. Detalles: {e}")
        return None

@st.cache_data(show_spinner="Cargando datos descriptivos...")
def load_descriptive_data():
    """Carga todos los archivos JSON y GeoJSON descriptivos."""
    stats, mun_resumen, tendencias, geojson_data = {}, {}, {}, {}
    try:
        # Carga de JSONs Descriptivos
        with open(get_file_path(BASE_DIR, "models", "descriptivo", "classification_dominant", "estadisticas_generales.json"), "r", encoding="utf-8") as f:
            stats = json.load(f)
        with open(get_file_path(BASE_DIR, "models", "descriptivo", "classification_dominant", "municipios_resumen.json"), "r", encoding="utf-8") as f:
            mun_resumen = json.load(f)
        with open(get_file_path(BASE_DIR, "models", "descriptivo", "classification_dominant", "tendencias_anuales.json"), "r", encoding="utf-8") as f:
            tendencias = json.load(f)
        
        # Carga de GeoJSON (Necesario para el Visor/Mapa)
        with open(get_file_path(BASE_DIR, "data", "silver", "dane_geo", "geografia_silver.geojson"), "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        # Añadir el nombre al resumen municipal para facilitar la búsqueda
        municipio_name_map = {}
        for feature in geojson_data.get("features", []):
            codigo = str(feature["properties"].get("codigo_municipio"))
            nombre = feature["properties"].get("municipio")
            if codigo and nombre:
                municipio_name_map[codigo] = nombre.upper()
                if codigo in mun_resumen:
                    mun_resumen[codigo]['nombre'] = nombre.upper() # Añadir nombre al JSON
        
        # Si Bucaramanga falta, lo añadimos si está en el resumen (código 68001)
        if "68001" in mun_resumen and "68001" not in municipio_name_map:
            municipio_name_map["68001"] = "BUCARAMANGA"
            mun_resumen["68001"]['nombre'] = "BUCARAMANGA"
        
        return stats, mun_resumen, tendencias, geojson_data, municipio_name_map

    except FileNotFoundError as e:
        st.error(f"Error al cargar archivos descriptivos: Asegúrese de que las carpetas 'models/descriptivo/...' y 'data/silver/...' existen y contienen todos los archivos necesarios. Detalles: {e}")
        return {}, {}, {}, {}, {}


# ============================
# FUNCIONES DE PREDICCIÓN Y RESPUESTA
# (Mantenemos la lógica de la versión anterior)
# ============================

def predecir_delito_arma(codigo_municipio, anio, mes, modelos, mun_resumen):
    """Ejecuta el modelo predictivo (Multi-Output) con features simuladas."""
    
    if modelos is None or "model" not in modelos:
        return {"error": "Modelos predictivos no cargados correctamente."}

    model = modelos["model"]
    scaler = modelos["scaler"]
    
    # Simulación de features (Usando el total_delitos del municipio como base)
    if codigo_municipio not in mun_resumen or not mun_resumen[codigo_municipio].get("total_delitos"):
        # Usamos un valor por defecto si no hay datos descriptivos
        base_count = 100 
    else:
        # Base de delitos del municipio (total de delitos / 10 para simular un conteo mensual promedio bajo)
        base_count = mun_resumen[codigo_municipio]["total_delitos"] / 10 

    features = {
        'anio': anio, 'mes': mes, 'codigo_municipio': int(codigo_municipio),
        'count_delito': base_count * np.random.uniform(0.9, 1.1),
        'count_arma': base_count * np.random.uniform(0.7, 1.3),
        'mes_sin': np.sin(2 * np.pi * mes / 12),
        'mes_cos': np.cos(2 * np.pi * mes / 12),
        'count_delito_lag1': base_count * np.random.uniform(0.9, 1.1),
        'count_delito_lag2': base_count * np.random.uniform(0.9, 1.1),
        'count_delito_lag3': base_count * np.random.uniform(0.9, 1.1),
        'count_arma_lag1': base_count * np.random.uniform(0.7, 1.3),
        'count_arma_lag2': base_count * np.random.uniform(0.7, 1.3),
        'count_arma_lag3': base_count * np.random.uniform(0.7, 1.3),
        'count_delito_ma3': base_count, 
        'count_arma_ma3': base_count, 
    }
    
    X = pd.DataFrame([features])
    
    # Asegurar el orden de las columnas según el scaler
    try:
        feature_order = modelos["scaler"].feature_names_in_.tolist()
        X = X[feature_order]
    except AttributeError:
        # Esto ocurre si scaler.joblib está corrupto o no se cargó correctamente
        return {"error": "Error de compatibilidad de features en el escalador."}


    try:
        X_scaled = scaler.transform(X)
        predicciones = model.predict(X_scaled)
        
        delito_pred = modelos["le_delito"].inverse_transform(predicciones[0, 0:1].astype(int).tolist())[0]
        arma_pred = modelos["le_arma"].inverse_transform(predicciones[0, 1:2].astype(int).tolist())[0]
        
        return {
            "delito_predicho": delito_pred.strip(),
            "arma_predicha": arma_pred.strip(),
        }
    except Exception as e:
        return {"error": f"Error durante la predicción: {e}"}


def generar_respuesta_chatbot(pregunta: str, codigo_municipio: str, stats: dict, mun_resumen: dict, modelos: dict) -> str:
    """Genera una respuesta descriptiva o predictiva basada en la pregunta."""
    pregunta = pregunta.lower()
    
    municipio_data = mun_resumen.get(codigo_municipio)

    # --- 1. Preguntas Predictivas (Futuro) ---
    if any(keyword in pregunta for keyword in ["futuro", "próximo mes", "pasará", "proyección", "esperar"]):
        
        if modelos is None:
             return "No puedo hacer predicciones, los modelos de Machine Learning no se cargaron correctamente."
             
        today = datetime.date.today()
        # Predecir el mes siguiente
        mes_pred = today.month % 12 + 1
        anio_pred = today.year + (1 if today.month == 12 else 0)
        
        pred = predecir_delito_arma(codigo_municipio, anio_pred, mes_pred, modelos, mun_resumen)
        
        if "error" in pred:
            return f"Lo siento, ocurrió un error al calcular la predicción: {pred['error']}"
        
        mun_name = municipio_data.get('nombre', 'El municipio')
        return f"Para el próximo mes ({mes_pred}/{anio_pred}) en {mun_name}, la proyección indica que el delito más frecuente será **{pred['delito_predicho']}**, con **{pred['arma_predicha']}** como arma dominante."

    # --- 2. Preguntas Descriptivas por Municipio (Pasado/Actual) ---
    if municipio_data:
        mun_name = municipio_data.get('nombre', 'Este municipio')
        
        if 'delito' in pregunta and 'común' in pregunta:
            return f"El delito más frecuente en {mun_name} es **{municipio_data['delito_mas_frecuente']}**."
        
        elif 'riesgo' in pregunta or 'seguro' in pregunta:
            return f"{mun_name} tiene un nivel de riesgo **{municipio_data['categoria_riesgo']}** y ocupa el puesto **#{municipio_data['ranking_departamental']}**."
        
        elif 'aumentado' in pregunta or 'tendencia' in pregunta:
            dir = municipio_data['tendencia']['direccion']
            cambio = municipio_data['tendencia']['cambio_vs_anio_anterior']
            return f"La criminalidad en {mun_name} está **{dir}** ({cambio:+.1f}% vs. año anterior)."
        
        elif 'información' in pregunta or 'general' in pregunta:
            return municipio_data.get('descripcion_chatbot', f"No tengo una descripción detallada para {mun_name}.")
            
    # --- 3. Preguntas Descriptivas Globales (Santander) ---
    if any(keyword in pregunta for keyword in ["santander", "departamento", "global"]):
        if 'delito' in pregunta and 'común' in pregunta:
            return f"El delito más frecuente en Santander es **{stats.get('delito_mas_frecuente', {}).get('nombre', 'N/A')}** ({stats.get('delito_mas_frecuente', {}).get('porcentaje', 0):.1f}% del total)."
        
        elif 'arma' in pregunta and 'común' in pregunta:
            return f"El arma más utilizada en Santander es **{stats.get('arma_mas_frecuente', {}).get('nombre', 'N/A')}** ({stats.get('arma_mas_frecuente', {}).get('porcentaje', 0):.1f}% del total)."
            
    return "Lo siento, no tengo información sobre esa pregunta específica. Asegúrate de que el municipio de enfoque sea el correcto."