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
# Asumimos que utils.py está al mismo nivel que app.py y 1_Visor_Analitico.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_file_path(relative_path):
    """Genera una ruta normalizada para cualquier sistema operativo."""
    # Los archivos de datos están en la carpeta superior ('..') desde el script de ejecución.
    return os.path.normpath(os.path.join(BASE_DIR, *relative_path))

MODEL_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "models", "predictivos", "classification_dominant")
)

# ============================
# FUNCIONES DE CARGA (Usadas en todos los scripts)
# ============================

@st.cache_resource(show_spinner="Cargando modelos predictivos...") 
def load_predictive_models():
    """Carga los modelos de predicción."""
    try:
        # Nota: La ruta real debe ser ajustada si su estructura de carpetas es diferente
        # Aquí asumimos que los joblib están en una carpeta 'models/predictivos/...'
        model = joblib.load(get_file_path(["models", "predictivos", "classification_dominant", "xgb_multioutput.joblib"]))
        le_delito = joblib.load(get_file_path(["models", "predictivos", "classification_dominant", "label_encoder_delito.joblib"]))
        le_arma = joblib.load(get_file_path(["models", "predictivos", "classification_dominant", "label_encoder_arma.joblib"]))
        scaler = joblib.load(get_file_path(["models", "predictivos", "classification_dominant", "scaler.joblib"]))
        
    except FileNotFoundError as e:
        st.error(f"Error al cargar joblib. Asegúrese de que los archivos estén en la ruta correcta. Detalles: {e}")
        return None
    except Exception as e:
        st.error(f"Error crítico al cargar componentes del modelo. Detalles: {e}")
        return None
    
    return {
        "model": model,
        "le_delito": le_delito,
        "le_arma": le_arma,
        "scaler": scaler
    }

@st.cache_data(show_spinner="Cargando datos descriptivos...")
def load_descriptive_data():
    """Carga todos los archivos JSON descriptivos."""
    try:
        with open(get_file_path(["models", "descriptivo", "classification_dominant", "estadisticas_generales.json"]), "r", encoding="utf-8") as f:
            stats = json.load(f)
        with open(get_file_path(["models", "descriptivo", "classification_dominant", "municipios_resumen.json"]), "r", encoding="utf-8") as f:
            mun_resumen = json.load(f)
        
        return stats, mun_resumen
    except FileNotFoundError as e:
        st.error(f"Error al cargar JSON descriptivos. Detalles: {e}")
        return {}, {}


# ============================
# FUNCIONES DE PREDICCIÓN Y RESPUESTA (Reutilizables)
# ============================

def predecir_delito_arma(codigo_municipio, anio, mes, modelos, mun_resumen):
    """
    Función predictiva (extraída del visor analítico) para ser usada por el chatbot.
    Requiere que los modelos y el resumen municipal estén cargados.
    """
    if modelos is None or "model" not in modelos:
        return "Modelos predictivos no cargados. No puedo predecir el futuro."

    model = modelos["model"]
    scaler = modelos["scaler"]

    # Simulación de features (Usando el total_delitos del municipio como base)
    if codigo_municipio not in mun_resumen:
        base_count = 100 # Default si no se encuentra
    else:
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
    feature_order = scaler.feature_names_in_.tolist()
    X = X[feature_order]

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
    """
    Genera una respuesta descriptiva (JSON) o predictiva (ML) basada en la pregunta.
    """
    pregunta = pregunta.lower()
    
    municipio_data = mun_resumen.get(codigo_municipio)

    # --- 1. Preguntas Predictivas (Futuro) ---
    if any(keyword in pregunta for keyword in ["futuro", "próximo mes", "pasará", "proyección"]):
        
        today = datetime.date.today()
        # Predecir el mes siguiente
        mes_pred = today.month % 12 + 1
        anio_pred = today.year + (1 if today.month == 12 else 0)
        
        pred = predecir_delito_arma(codigo_municipio, anio_pred, mes_pred, modelos, mun_resumen)
        
        if "error" in pred:
            return f"Lo siento, ocurrió un error al calcular la predicción para {municipio_data.get('nombre', 'el municipio')}: {pred['error']}"
        
        return f"Para el próximo mes ({mes_pred}/{anio_pred}), la proyección indica que el delito más frecuente será **{pred['delito_predicho']}**, con **{pred['arma_predicha']}** como arma dominante."

    # --- 2. Preguntas Descriptivas por Municipio (Pasado/Actual) ---
    if municipio_data:
        mun_name = municipio_data.get('nombre', 'Este municipio') # Necesita el nombre del municipio
        
        if 'delito' in pregunta and 'común' in pregunta:
            return f"El delito más frecuente en {mun_name} es **{municipio_data['delito_mas_frecuente']}**."
        
        elif 'riesgo' in pregunta or 'seguro' in pregunta:
            return f"{mun_name} tiene un nivel de riesgo **{municipio_data['categoria_riesgo']}** y ocupa el puesto **#{municipio_data['ranking_departamental']}**."
        
        elif 'aumentado' in pregunta or 'tendencia' in pregunta:
            dir = municipio_data['tendencia']['direccion']
            cambio = municipio_data['tendencia']['cambio_vs_anio_anterior']
            return f"La criminalidad en {mun_name} está **{dir}** ({cambio:+.1f}% vs. año anterior)."
        
        elif 'información' in pregunta or 'general' in pregunta:
            return municipio_data['descripcion_chatbot']
            
    # --- 3. Preguntas Descriptivas Globales (Santander) ---
    if any(keyword in pregunta for keyword in ["santander", "departamento", "global"]):
        if 'delito' in pregunta and 'común' in pregunta:
            return f"El delito más frecuente en Santander es **{stats['delito_mas_frecuente']['nombre']}** ({stats['delito_mas_frecuente']['porcentaje']:.1f}% del total)."
        
        elif 'arma' in pregunta and 'común' in pregunta:
            return f"El arma más utilizada en Santander es **{stats['arma_mas_frecuente']['nombre']}** ({stats['arma_mas_frecuente']['porcentaje']:.1f}% del total)."
            
    return "Lo siento, no tengo información sobre esa pregunta específica. Intenta preguntar sobre el riesgo, el delito más común o la tendencia de un municipio."