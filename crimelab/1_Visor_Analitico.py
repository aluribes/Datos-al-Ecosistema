import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from branca.element import MacroElement, Template
import numpy as np 
import datetime

from utils import draw_sidebar_menu, load_predictive_models, load_descriptive_data, inject_styles


# ------------------------------------------------------------------------------
# 1. Carga de Datos y Modelos (Centralizado en utils.py)
# ------------------------------------------------------------------------------

# Carga de Modelos Predictivos (se realiza UNA sola vez gracias a st.cache_resource en utils)
modelos_predictivos = load_predictive_models()

# Carga de Datos Descriptivos y Geoespaciales (se realiza UNA sola vez gracias a st.cache_data en utils)
# La función load_descriptive_data devuelve: 
# stats, mun_resumen, tendencias, geojson_data, municipio_name_map
stats, mun_resumen, tendencias_raw, geojson_data, municipio_name_map = load_descriptive_data()

# Verificación de carga
if not stats or not modelos_predictivos or not geojson_data:
    st.error("🚨 **Error Crítico:** No se pudo cargar la información esencial (stats, modelos o datos geográficos). Revise las rutas de los archivos en 'utils.py'.")
    st.stop() # Detener la ejecución si faltan datos cruciales.


# ------------------------------------------------------------------------------
# 2. Funciones de Visualización y Lógica (Se mantienen aquí)
# ------------------------------------------------------------------------------

def plot_tendencia_anual(tendencias_data, año_referencia):
    # La lógica de esta función se mantiene sin cambios
    df_tend = pd.DataFrame({
        "Año": list(tendencias_data["delitos_por_anio"].keys()),
        "Delitos": list(tendencias_data["delitos_por_anio"].values())
    })
    df_tend["Año"] = df_tend["Año"].astype(int)
    max_anio_historico = df_tend["Año"].max()
    
    # Manejo del caso donde el año de referencia es el último año cargado (proyección)
    df_tend["Tipo"] = np.where(df_tend["Año"] > max_anio_historico - 1, "Proyección", "Histórico")

    fig = px.line(df_tend, x="Año", y="Delitos", title=f"Tendencia Histórica de Delitos (Resaltando Año {año_referencia})", markers=True, color="Tipo", color_discrete_map={"Histórico": "#1f77b4", "Proyección": "#e74c3c"})
    
    if año_referencia in df_tend["Año"].values:
        fig.add_vline(x=año_referencia, line_width=2, line_dash="dash", line_color="gray", annotation_text=f"Año de análisis: {año_referencia}", annotation_position="top left")

    fig.update_traces(marker=dict(size=8))
    fig.update_layout(title_font=dict(size=24, family="Arial", color="#333"), xaxis_title="Año", yaxis_title="Número de Delitos", hovermode="x unified", legend_title_text='Datos', height=500)
    return fig


def plot_distribucion_delitos(stats_data):
    # La lógica de esta función se mantiene sin cambios
    if "distribucion_delitos" not in stats_data or not stats_data["distribucion_delitos"]: 
        return None
        
    delitos_data = {
        delito: data.get("porcentaje", 0) 
        for delito, data in stats_data["distribucion_delitos"].items()
    }

    df_dist = pd.DataFrame(list(delitos_data.items()), columns=['Delito', 'Porcentaje'])
    
    df_dist['Porcentaje'] = df_dist['Porcentaje'].astype(float) 
    # Normalizar para asegurar que sume 100% si los datos ya no están normalizados (aunque no se necesita si ya son porcentajes)
    if df_dist['Porcentaje'].sum() > 100 or df_dist['Porcentaje'].sum() < 90:
        # Se asume que el porcentaje en el JSON está en formato XX.XX (%)
        df_dist['Porcentaje'] = df_dist['Porcentaje'] / 100.0 # Ajuste si fuera necesario usar la proporción para Plotly
    
    fig = px.pie(df_dist, values='Porcentaje', names='Delito', title='Distribución Global de Delitos Dominantes en Santander', hole=0.4)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title_font=dict(size=22, family="Arial", color="#333"), uniformtext_minsize=12, uniformtext_mode='hide', legend_title_text='Tipos de Delito')
    return fig

COLOR_RIESGO = {"Alto": "#e74c3c", "Medio-Alto": "#e67e22", "Medio-Bajo": "#f1c40f", "Bajo": "#2ecc71"}
def get_color(riesgo):
    return COLOR_RIESGO.get(riesgo, "#bdc3c7")

def predecir_delito_arma(codigo_municipio, anio, mes, modelos):
    """Ejecuta el modelo predictivo con features simuladas. Usa el mun_resumen cargado globalmente."""
    
    if modelos is None or "model" not in modelos:
        return {"error": "Modelos predictivos no cargados correctamente."}

    # Acceso directo a los componentes del modelo
    model = modelos["model"]
    scaler = modelos["scaler"]
    le_delito = modelos["le_delito"]
    le_arma = modelos["le_arma"]
    
    # mun_resumen y otros datos se acceden desde el ámbito global de este script
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
    
    try:
        # Asegurar el orden de las columnas según el scaler (CRÍTICO)
        feature_order = scaler.feature_names_in_.tolist()
        X = X[feature_order]

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

# Aplicar estilos y menú (se ejecuta en cada página)
inject_styles()
draw_sidebar_menu()

st.title("🗺️ Visor Analítico de Seguridad Ciudadana")

# Definir Pestañas
tab_descriptivo, tab_predictivo = st.tabs(["Históricos", "Proyecciones"])

# Generar DataFrame de municipios para el ranking y el mapa (una sola vez)
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
# PESTAÑA 1: MODELO DESCRIPTIVO
# ------------------------------------------------------------------------------
with tab_descriptivo:
    
    # === 1. INDICADORES GLOBALES ===
    st.header("📊 Indicadores Globales de Santander")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Delito más frecuente", stats["delito_mas_frecuente"]["nombre"], delta=f"{stats['delito_mas_frecuente']['porcentaje']:.1f}% del total")
    col2.metric("Arma más frecuente", stats["arma_mas_frecuente"]["nombre"], delta=f"{stats['arma_mas_frecuente']['porcentaje']:.1f}% del total")
    col3.metric("Total delitos dominantes", f"{stats['suma_delitos_dominantes']:,}")
    
    # Tendencia General
    cambio_vs_anterior = tendencias_raw['cambio_porcentual'].get(str(stats['periodo']['fin'] - 1), 0)
    col4.metric("Tendencia General", tendencias_raw['tendencia_general'].capitalize(), delta=f"Cambio vs año anterior: {cambio_vs_anterior:.1f}%")

    st.markdown("---")

    # === 2. MAPA DE RIESGO ===
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

    # Leyenda (MacroElement) - La lógica se mantiene sin cambios
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
    st.header("Predicción del Delito y Arma Dominante por Municipio")

    if modelos_predictivos is None:
        st.warning("⚠️ **ATENCIÓN:** La predicción está deshabilitada porque los archivos `.joblib` no pudieron ser cargados correctamente. Verifique si los archivos están en las rutas definidas en `utils.py`.")
    else:
        # F I L T R O S P R E D I C T I V O S
        with st.container(border=True):
            st.subheader("📅 Controles de Predicción")
            col_mun, col_mes, col_anio, col_btn = st.columns([2, 1, 1, 1])
            
            municipios_predict = sorted(list(municipio_name_map.values()))
            municipio_pred_name = col_mun.selectbox("Selecciona un municipio para predecir:", municipios_predict, key="mun_pred")
            
            # Obtener el código DANE del municipio seleccionado
            codigo_municipio_pred = next((k for k, v in municipio_name_map.items() if v == municipio_pred_name), None)

            # Cálculo de fecha de predicción (mes siguiente por defecto)
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
                        # Llamada a la función predictiva (que usa los modelos cargados)
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
                **Análisis Descriptivo (Histórico):**
                * Riesgo: **{riesgo}**
                * Puesto: **#{puesto}**
                * Delito Histórico: **{mun_info.get("delito_mas_frecuente", "N/A")}**
                """)
                
                st.warning(f"🚨 **ALERTA:** Se predice que el **{pred['delito_predicho']}** será el mayor riesgo para este municipio, principalmente usando **{pred['arma_predicha']}**.")

        else:
            st.info("Utiliza los controles de predicción de arriba para obtener el resultado del modelo predictivo.")