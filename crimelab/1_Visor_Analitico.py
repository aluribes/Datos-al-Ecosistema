import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from branca.element import MacroElement, Template
import numpy as np 
import joblib 
import datetime

# ------------------------------------------------------------------------------
# 1. Lógica de Carga de Archivos y Corrección de Rutas
# ------------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Definir la ruta donde se encuentran todos los archivos .joblib
MODEL_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "..", "models", "predictivos", "classification_dominant")
)

def get_file_path(relative_path):
    """Genera una ruta normalizada para cualquier sistema operativo."""
    return os.path.normpath(os.path.join(BASE_DIR, *relative_path))

# Funciones de carga (usando la ruta robusta)
def load_stats():
    ruta_json = get_file_path(["..", "models", "descriptivo", "classification_dominant", "estadisticas_generales.json"])
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)

def load_tendencias():
    ruta_json = get_file_path(["..", "models", "descriptivo", "classification_dominant", "tendencias_anuales.json"])
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)

def load_municipios():
    json_path = get_file_path(["..", "models", "descriptivo", "classification_dominant", "municipios_resumen.json"])
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_geojson():
    geojson_path = get_file_path(["..", "data", "silver", "dane_geo", "geografia_silver.geojson"])
    with open(geojson_path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_resource(show_spinner="Cargando modelos predictivos...") 
def load_predictive_models(model_path):
    """Carga los modelos Predictivos usando la ruta explícita o el nombre simple si falla la ruta."""
    try:
        # Intento 1: Usar la ruta completa proporcionada por el usuario
        model = joblib.load(os.path.join(model_path, "xgb_multioutput.joblib"))
        le_delito = joblib.load(os.path.join(model_path, "label_encoder_delito.joblib"))
        le_arma = joblib.load(os.path.join(model_path, "label_encoder_arma.joblib"))
        scaler = joblib.load(os.path.join(model_path, "scaler.joblib"))
        
    except FileNotFoundError:
        # Intento 2 (Fallback): Si falla la ruta completa, intentar cargarlos directamente por nombre de archivo
        st.warning("Ruta de modelo compleja fallida. Intentando cargar modelos directamente por nombre de archivo.")
        model = joblib.load("xgb_multioutput.joblib")
        le_delito = joblib.load("label_encoder_delito.joblib")
        le_arma = joblib.load("label_encoder_arma.joblib")
        scaler = joblib.load("scaler.joblib")
    except Exception as e:
        st.error(f"Error crítico al cargar componentes del modelo. Detalles: {e}")
        return None
    
    return {
        "model": model,
        "le_delito": le_delito,
        "le_arma": le_arma,
        "scaler": scaler
    }

# Cargamos los modelos predictivos una sola vez al inicio.
model_components = load_predictive_models(MODEL_PATH)


# Cachear la carga de datos
@st.cache_data(show_spinner="Cargando datos...")
def get_data(_modelos_cargados):
    stats = load_stats()
    tendencias = load_tendencias()
    mun_resumen = load_municipios()
    geojson_data = load_geojson()

    municipio_name_map = {}
    for feature in geojson_data["features"]:
        codigo = str(feature["properties"].get("codigo_municipio"))
        nombre = feature["properties"].get("municipio")
        if codigo and nombre:
            municipio_name_map[codigo] = nombre
    
    if "68001" in mun_resumen and "68001" not in municipio_name_map:
        municipio_name_map["68001"] = "BUCARAMANGA" 
    
    return {
        "stats": stats,
        "tendencias": tendencias,
        "municipios_resumen": mun_resumen,
        "geojson": geojson_data,
        "municipio_name_map": municipio_name_map,
        "modelos_predictivos": _modelos_cargados
    }

# Pasamos los modelos cargados a la función de caché de datos.
data = get_data(model_components)

stats = data["stats"]
tendencias_raw = data["tendencias"]
mun_resumen = data["municipios_resumen"]
geojson_data = data["geojson"]
municipio_name_map = data["municipio_name_map"]
modelos_predictivos = data["modelos_predictivos"]

# ------------------------------------------------------------------------------
# 2. Funciones de Visualización y Lógica
# ------------------------------------------------------------------------------

def plot_tendencia_anual(tendencias_data, año_referencia):
    df_tend = pd.DataFrame({
        "Año": list(tendencias_data["delitos_por_anio"].keys()),
        "Delitos": list(tendencias_data["delitos_por_anio"].values())
    })
    df_tend["Año"] = df_tend["Año"].astype(int)
    max_anio_historico = df_tend["Año"].max()
    
    df_tend["Tipo"] = np.where(df_tend["Año"] > max_anio_historico - 1, "Proyección", "Histórico")

    fig = px.line(df_tend, x="Año", y="Delitos", title=f"Tendencia Histórica de Delitos (Resaltando Año {año_referencia})", markers=True, color="Tipo", color_discrete_map={"Histórico": "#1f77b4", "Proyección": "#e74c3c"})
    
    if año_referencia in df_tend["Año"].values:
        fig.add_vline(x=año_referencia, line_width=2, line_dash="dash", line_color="gray", annotation_text=f"Año de análisis: {año_referencia}", annotation_position="top left")

    fig.update_traces(marker=dict(size=8))
    fig.update_layout(title_font=dict(size=24, family="Arial", color="#333"), xaxis_title="Año", yaxis_title="Número de Delitos", hovermode="x unified", legend_title_text='Datos', height=500)
    return fig


def plot_distribucion_delitos(stats_data):
    # CORRECCIÓN IMPORTANTE: Extraemos solo el porcentaje del diccionario anidado.
    if "distribucion_delitos" not in stats_data or not stats_data["distribucion_delitos"]: 
        return None
        
    # Extraer el nombre del delito y su porcentaje.
    delitos_data = {
        delito: data.get("porcentaje", 0) 
        for delito, data in stats_data["distribucion_delitos"].items()
    }

    # Convertir a DataFrame
    df_dist = pd.DataFrame(list(delitos_data.items()), columns=['Delito', 'Porcentaje'])
    
    # Aseguramos el tipo float para el porcentaje y normalizamos si es necesario
    df_dist['Porcentaje'] = df_dist['Porcentaje'].astype(float) 
    df_dist['Porcentaje'] = df_dist['Porcentaje'] / df_dist['Porcentaje'].sum()
    
    fig = px.pie(df_dist, values='Porcentaje', names='Delito', title='Distribución Global de Delitos Dominantes en Santander', hole=0.4)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title_font=dict(size=22, family="Arial", color="#333"), uniformtext_minsize=12, uniformtext_mode='hide', legend_title_text='Tipos de Delito')
    return fig

COLOR_RIESGO = {"Alto": "#e74c3c", "Medio-Alto": "#e67e22", "Medio-Bajo": "#f1c40f", "Bajo": "#2ecc71"}
def get_color(riesgo):
    return COLOR_RIESGO.get(riesgo, "#bdc3c7")

def predecir_delito_arma(codigo_municipio, anio, mes, modelos):
    """Ejecuta el modelo predictivo con features simuladas."""
    
    if modelos is None or "model" not in modelos:
        return {"error": "Modelos predictivos no cargados correctamente."}

    model = modelos["model"]
    scaler = modelos["scaler"]
    le_delito = modelos["le_delito"]
    le_arma = modelos["le_arma"]
    
    if codigo_municipio not in mun_resumen:
        return {"error": "Municipio no encontrado en el resumen descriptivo."}

    # Usamos el total de delitos del municipio descriptivo como base para la simulación
    base_count = mun_resumen[codigo_municipio]["total_delitos"] / 10 

    # --- Creación de Features (con simulación) ---
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
    feature_order = scaler.feature_names_in_.tolist()
    X = X[feature_order]

    try:
        X_scaled = scaler.transform(X)
        predicciones = model.predict(X_scaled)
        
        delito_pred = le_delito.inverse_transform(predicciones[0, 0:1].astype(int).tolist())[0]
        arma_pred = le_arma.inverse_transform(predicciones[0, 1:2].astype(int).tolist())[0]
        
        return {
            "delito_predicho": delito_pred.strip(),
            "arma_predicha": arma_pred.strip(),
            "mes": mes,
            "anio": anio
        }
    except Exception as e:
        return {"error": f"Error durante la predicción: {e}"}

# ------------------------------------------------------------------------------
# 3. Configuración y Layout Principal
# ------------------------------------------------------------------------------

st.set_page_config(
    page_title="Visor Analítico – CrimeLab",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Visor Analítico de Seguridad Ciudadana")

# Definir Pestañas
tab_descriptivo, tab_predictivo = st.tabs(["Históricos", "Proyecciones"])

# Generar DataFrame de municipios para el ranking y el mapa (se hace una sola vez)
df_mun = pd.DataFrame([
    {
        "Código DANE": k,
        "Municipio": municipio_name_map.get(k, f"Código {k} (Sin nombre)"), 
        "Ranking": v["ranking_departamental"],
        "Riesgo": v["categoria_riesgo"],
        "Delito Dominante": v["delito_mas_frecuente"], 
        "Total Delitos": v["total_delitos"]
    }
    for k, v in mun_resumen.items()
]).sort_values("Ranking")


# ------------------------------------------------------------------------------
# PESTAÑA 1: MODELO DESCRIPTIVO (Orden Corregido)
# ------------------------------------------------------------------------------
with tab_descriptivo:
    
    # === 1. INDICADORES GLOBALES (PRIMERO) ===
    st.header("📊 Indicadores Globales de Santander")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Delito más frecuente", stats["delito_mas_frecuente"]["nombre"], delta=f"{stats['delito_mas_frecuente']['porcentaje']:.1f}% del total")
    col2.metric("Arma más frecuente", stats["arma_mas_frecuente"]["nombre"], delta=f"{stats['arma_mas_frecuente']['porcentaje']:.1f}% del total")
    col3.metric("Total delitos dominantes", f"{stats['suma_delitos_dominantes']:,}")
    # Nota: Se usa el año anterior al final del periodo para la tendencia general. 
    # El dato de 'cambio_porcentual' es un diccionario, se accede con la clave del año.
    cambio_vs_anterior = tendencias_raw['cambio_porcentual'].get(str(stats['periodo']['fin']-1), 0)
    col4.metric("Tendencia General", tendencias_raw['tendencia_general'].capitalize(), delta=f"Cambio vs año anterior: {cambio_vs_anterior:.1f}%")

    st.markdown("---")

    # === 2. MAPA DE RIESGO (SEGUNDO, POSICIÓN ORIGINAL DE DISTRIBUCIÓN) ===
    st.header("🗺️ Mapa de Clasificación de Riesgo - Santander")
    
    m = folium.Map(location=[7.12539, -73.1198], zoom_start=8, tiles="CartoDB positron")
    
    mun_dict = df_mun.set_index("Código DANE").T.to_dict()

    for feature in geojson_data["features"]:
        codigo = str(feature["properties"].get("codigo_municipio"))
        nombre_mun = feature["properties"].get("municipio", "-")

        if codigo in mun_dict:
            row = mun_dict[codigo]
            color = get_color(row["Riesgo"])
            riesgo = row["Riesgo"]
            delito = row["Delito Dominante"]
            delitos = row["Total Delitos"]
        else:
            color = "#bdc3c7"
            riesgo = "Sin datos"
            delito = "-"
            delitos = "0"

        popup_html = f"""
        <div style="font-size: 14px;">
            <b>Municipio:</b> {nombre_mun}<br>
            <b>Riesgo:</b> <span style='color:{color}; font-weight:bold;'>{riesgo}</span><br>
            <b>Total delitos:</b> {delitos:,}<br>
            <b>Delito dominante:</b> {delito}
        </div>
        """

        folium.GeoJson(
            feature, name=nombre_mun,
            style_function=lambda x, col=color: {
                "fillColor": col, "color": "black", "weight": 1, "fillOpacity": 0.7
            },
            tooltip=folium.Tooltip(popup_html, sticky=True)
        ).add_to(m)

    # Leyenda (MacroElement)
    template = """
    {% macro html(this, kwargs) %}
    <div style="position: fixed; bottom: 50px; left: 50px; width: 140px; height: 140px; background-color: white; border: 1px solid gray; padding: 5px; z-index:9999; font-size:14px;">
        <b>Clasificación de Riesgo:</b><br>
        <i style="background:#e74c3c;width:18px;height:18px;display:inline-block"></i> Alto<br>
        <i style="background:#e67e22;width:18px;height:18px;display:inline-block"></i> Medio-Alto<br>
        <i style="background:#f1c40f;width:18px;height:18px;display:inline-block"></i> Medio-Bajo<br>
        <i style="background:#2ecc71;width:18px;height:18px;display:inline-block"></i> Bajo<br>
        <i style="background:#bdc3c7;width:18px;height:18px;display:inline-block"></i> Sin datos
    </div>
    {% endmacro %}
    """
    macro = MacroElement()
    macro._template = Template(template)
    m.get_root().add_child(macro)

    st_folium(m, width=900, height=550)
    
    st.markdown("---")


    # === 3. Distribución de Delitos ===
    st.subheader("Distribución Global de Delitos")
    fig_distribucion = plot_distribucion_delitos(stats)
    
    if fig_distribucion:
        st.plotly_chart(fig_distribucion, use_container_width=True)
    else:
        st.info("La distribución global de delitos no está disponible en los datos cargados o la sección está vacía.")
    
    st.markdown("---")

    # === 4. Análisis de Tendencia (Solo Tendencia Anual) ===
    st.header("⏳ Análisis de Tendencia Anual")
    
    # F I L T R O (Solo Año)
    with st.container(border=True): 
        st.subheader("🎛️ Controles de Exploración")
        col_anho, col_vacio = st.columns([1, 3])

        años_disponibles = sorted(list(set(range(2010, 2026)))) 
        año_selected = col_anho.selectbox("Año de Referencia:", años_disponibles, index=len(años_disponibles)-1, key="anio_desc")
        
    # Visualización de Tendencia
    fig_tendencia = plot_tendencia_anual(tendencias_raw, año_selected)
    st.plotly_chart(fig_tendencia, use_container_width=True)

    st.markdown("---")

    # === 5. Ranking ===
    st.header("🏅 Ranking de Criminalidad Municipal")
    
    col_rank_settings, col_rank_table = st.columns([1, 3])
    with col_rank_settings:
        top_n = st.slider("Mostrar TOP N municipios", 5, 30, 10, key="top_n_desc")
    with col_rank_table:
        df_top = df_mun.head(top_n).set_index("Ranking")
        st.dataframe(df_top, use_container_width=True)


# ------------------------------------------------------------------------------
# PESTAÑA 2: MODELO PREDICTIVO
# ------------------------------------------------------------------------------
with tab_predictivo:
    st.header("🔮 Predicción del Delito y Arma Dominante por Municipio")

    if modelos_predictivos is None:
        st.warning("⚠️ **ATENCIÓN:** La predicción está deshabilitada porque los archivos `.joblib` no pudieron ser cargados correctamente. Consulte los mensajes de error al inicio para verificar la ruta.")
    else:
        # F I L T R O S P R E D I C T I V O S
        with st.container(border=True):
            st.subheader("📅 Controles de Predicción")
            col_mun, col_mes, col_anio, col_btn = st.columns([2, 1, 1, 1])
            
            municipios_predict = sorted(list(municipio_name_map.values()))
            municipio_pred_name = col_mun.selectbox("Selecciona un municipio para predecir:", municipios_predict, key="mun_pred")
            
            codigo_municipio_pred = next((k for k, v in municipio_name_map.items() if v == municipio_pred_name), None)

            # Cálculo de fecha de predicción (mes siguiente)
            today = datetime.date.today()
            mes_pred_val = today.month % 12 + 1
            anio_pred_val = today.year + (1 if today.month == 12 else 0)
            
            meses_disp = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                          7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

            mes_pred = col_mes.number_input(f"Mes ({meses_disp.get(mes_pred_val)})", min_value=1, max_value=12, value=mes_pred_val, key="mes_pred")
            anio_pred = col_anio.number_input("Año", min_value=today.year, max_value=today.year + 10, value=anio_pred_val, key="anio_pred")

            # Botón para ejecutar la predicción
            if col_btn.button("Ejecutar Predicción 🚀"):
                if codigo_municipio_pred and codigo_municipio_pred in mun_resumen:
                    with st.spinner(f"Calculando predicción para **{municipio_pred_name}** en **{meses_disp.get(mes_pred)}/{anio_pred}**..."):
                        resultado = predecir_delito_arma(str(codigo_municipio_pred), int(anio_pred), int(mes_pred), modelos_predictivos)
                        st.session_state["prediccion_actual"] = resultado
                else:
                    st.error("Selecciona un municipio válido.")

        st.markdown("---")

        # R E S U L T A D O S
        st.subheader("Resultado de la Predicción")
        
        if "prediccion_actual" in st.session_state:
            pred = st.session_state["prediccion_actual"]
            
            if "error" in pred:
                st.error(f"Error en el modelo: {pred['error']}")
            else:
                st.success(f"Predicción exitosa para **{municipio_pred_name}** en **{meses_disp.get(pred['mes'])}/{pred['anio']}**:")
                
                col_delito, col_arma, col_desc = st.columns(3)
                
                col_delito.metric("Delito Dominante Predicho", pred["delito_predicho"])
                col_arma.metric("Arma Dominante Predicha", pred["arma_predicha"])
                
                mun_info = mun_resumen.get(codigo_municipio_pred, {})
                riesgo = mun_info.get("categoria_riesgo", "N/A")
                puesto = mun_info.get("ranking_departamental", "N/A")

                col_desc.info(f"""
                **Análisis Descriptivo (Actual):**
                * Riesgo: **{riesgo}**
                * Puesto: **#{puesto}**
                * Delito Histórico: **{mun_info.get("delito_mas_frecuente", "N/A")}**
                """)
                
                st.warning(f"🚨 **ALERTA:** Se predice que el **{pred['delito_predicho']}** será el mayor riesgo para este municipio, principalmente usando **{pred['arma_predicha']}**.")

        else:
            st.info("Utiliza los controles de predicción de arriba para obtener el resultado del modelo predictivo.")




