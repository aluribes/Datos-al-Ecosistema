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
# Importación de todas las funciones esenciales desde utils.py
from utils import draw_sidebar_menu, load_predictive_models, load_descriptive_data, inject_styles

# NOTA: La función predecir_delito_arma se mantiene aquí, pero asume los datos del modelo dominante
# Si se quisiera agregar predicción para Event, se necesitaría una nueva función con los features del modelo Event.
# Por ahora, solo integramos la parte descriptiva.

# ------------------------------------------------------------------------------
# 1. Carga de Datos y Modelos (Centralizado en utils.py)
# ------------------------------------------------------------------------------

# Carga de Modelos Predictivos DOMINANT
modelos_predictivos = load_predictive_models()

# Carga de Datos Descriptivos y Geoespaciales (Dual)
data_load_result = load_descriptive_data()

# Desempaquetamiento (4 valores)
data_dominant, data_event, geojson_data, municipio_name_map = data_load_result

# Asignación para Modelo DOMINANT (Mantener la funcionalidad existente)
stats = data_dominant["stats"]
mun_resumen = data_dominant["mun_resumen"]
tendencias_raw = data_dominant["tendencias"]

# Asignación para Modelo EVENT
resumen_event = data_event["resumen"] 
distribucion_delitos_event = data_event["distribucion_delitos"]
distribucion_perfiles_event = data_event["distribucion_perfiles"]
demografico_event = data_event["demografico"] 
geografico_event = data_event["geografico"] 
cruces_delito_perfil_event = data_event["cruces_delito_perfil"]
top_combinaciones_event = data_event["top_combinaciones"]

# Extracción de métrica faltante de resumen_general.json (se saca de distribucion_delitos_event)
delito_mas_comun_event = distribucion_delitos_event["delito_mas_comun"]["nombre"]

# >>>>>>>>>>>>>>>>>>>>>>>>> INICIO DE CORRECCIÓN <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# CORRECCIÓN: La lista de delitos debe obtenerse de resumen_event (resumen_general.json)
if "tipos_delito" in resumen_event and "tipos" in resumen_event["tipos_delito"]:
    listado_delitos = sorted(resumen_event["tipos_delito"]["tipos"])
else:
    # Lógica de respaldo si la clave correcta no está disponible
    try:
        listado_delitos = sorted(list(distribucion_delitos_event["distribucion_delitos"].keys()))
    except:
        listado_delitos = []
# >>>>>>>>>>>>>>>>>>>>>>>>> FIN DE CORRECCIÓN <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# ------------------------------------------------------------------------------
# 2. Funciones de Visualización y Lógica (Modificadas)
# ------------------------------------------------------------------------------

def plot_tendencia_anual(tendencias_data, año_referencia):
    # La lógica de esta función se mantiene sin cambios
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
    # La lógica de esta función se mantiene sin cambios
    if "distribucion_delitos" not in stats_data or not stats_data["distribucion_delitos"]: 
        return None
        
    delitos_data = {
        delito: data.get("porcentaje", 0) 
        for delito, data in stats_data["distribucion_delitos"].items()
    }

    df_dist = pd.DataFrame(list(delitos_data.items()), columns=['Delito', 'Porcentaje'])
    
    df_dist['Porcentaje'] = df_dist['Porcentaje'].astype(float) 
    
    # Normalización simple si los porcentajes son grandes
    if df_dist['Porcentaje'].sum() > 100 or df_dist['Porcentaje'].sum() < 90:
        df_dist['Porcentaje'] = df_dist['Porcentaje'] / df_dist['Porcentaje'].sum()
    
    fig = px.pie(df_dist, values='Porcentaje', names='Delito', title='Distribución Global de Delitos Dominantes en Santander', hole=0.4)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title_font=dict(size=22, family="Arial", color="#333"), uniformtext_minsize=12, uniformtext_mode='hide', legend_title_text='Tipos de Delito')
    return fig

COLOR_RIESGO = {"Alto": "#e74c3c", "Medio-Alto": "#e67e22", "Medio-Bajo": "#f1c40f", "Bajo": "#2ecc71"}
def get_color(riesgo):
    return COLOR_RIESGO.get(riesgo, "#bdc3c7")

def predecir_delito_arma(codigo_municipio, anio, mes, modelos):
    """Ejecuta el modelo predictivo con features simuladas (Modelo Dominante)."""
    # ... (La lógica de predicción del modelo Dominante se mantiene igual)
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
    
    try:
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

# --- FUNCIONES DE VISUALIZACIÓN PARA MODELO EVENT ---

def plot_distribucion_event_delitos(data):
    """Gráfico de barras para distribución de delitos del Modelo Event."""
    if 'distribucion' not in data or not data['distribucion']:
        return None
    
    df = pd.DataFrame(data['distribucion'])
    df = df.sort_values(by='cantidad', ascending=False)
    
    fig = px.bar(df, x='delito', y='cantidad', title='Distribución de Delitos - Clasificación de Eventos', 
                 labels={'delito': 'Tipo de Delito', 'cantidad': 'Cantidad'},
                 color='delito', height=450)
    fig.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    return fig

def plot_perfiles(data_global, cruces_data, filtro_delito="Delitos Totales"):
    """
    Gráfico de barras horizontales para distribución de perfiles (Agresor/Víctima)
    con categorías unificadas, filtrado por delito. (CONFIRMADA Y AJUSTADA)
    """
    
    # --- Agrupación de categorías Helper ---
    def agrupar_perfil(perfil):
        perfil = str(perfil).upper().strip()
        # Agrupa categorías que indican falta de reporte
        if 'NO REPORTADO' in perfil or 'NO REPORTA' in perfil or 'NAN' in perfil or 'NONE' in perfil:
            return 'NO REPORTADO/NO ESPECIFICADO'
        return perfil
        
    if filtro_delito == "Delitos Totales":
        # Usar la distribución global (porcentaje)
        if 'distribucion' not in data_global or not data_global['distribucion']:
            return None
        df = pd.DataFrame(data_global['distribucion'])
        df['porcentaje'] = df['porcentaje'].astype(float)
        df['valor'] = df['porcentaje']
        
    else:
        # Usar la distribución por delito específico (porcentaje de cruce)
        if 'cruce_porcentual' not in cruces_data or filtro_delito not in cruces_data['cruce_porcentual']:
            return None
        
        # Convertir el diccionario de perfiles/porcentajes a DataFrame
        # Accede a la clave del delito solicitado
        perfiles_porcentaje = cruces_data['cruce_porcentual'][filtro_delito]
        df = pd.DataFrame(perfiles_porcentaje.items(), columns=['perfil', 'porcentaje'])
        df['valor'] = df['porcentaje'].astype(float)
        
    # --- Aplicación de Agrupación ---
    df['perfil_agrupado'] = df['perfil'].apply(agrupar_perfil)
    
    # Sumar valores (porcentaje) por el nuevo perfil agrupado
    df_grouped = df.groupby('perfil_agrupado').agg(
        valor=('valor', 'sum')
    ).reset_index()

    # Usar el valor sumado como porcentaje
    df_grouped['porcentaje'] = df_grouped['valor']
    df_grouped['porcentaje_label'] = df_grouped['porcentaje'].round(1).astype(str) + '%'
    
    df_grouped = df_grouped.sort_values(by='porcentaje', ascending=True)

    # El título del gráfico cambia para reflejar el filtro
    titulo_grafico = f'Distribución de Perfiles Agrupados: **{filtro_delito}**'
    
    fig = px.bar(df_grouped, x='porcentaje', y='perfil_agrupado', 
                 orientation='h',
                 title=titulo_grafico, 
                 labels={'perfil_agrupado': 'Perfil (Género y Edad)', 'porcentaje': 'Porcentaje'},
                 height=500,
                 color='perfil_agrupado')
                 
    fig.update_traces(text=df_grouped['porcentaje_label'], textposition='outside')
    fig.update_layout(showlegend=False,
                      xaxis_title="Porcentaje", 
                      yaxis_title="Perfiles Agrupados",
                      xaxis_tickformat=".1f", 
                      uniformtext_minsize=12, uniformtext_mode='hide')
                      
    return fig


def plot_demografico_etario(demografico_data, cruces_data, filtro_delito="Delitos Totales"):
    """
    Gráfico de barras para distribución por grupo etario, filtrado por delito. (CORREGIDO)
    """
    
    if filtro_delito == "Delitos Totales":
        # Usar la distribución global (cantidad)
        if demografico_data and 'por_grupo_etario' in demografico_data and 'distribucion' in demografico_data['por_grupo_etario']:
            distribucion_edad = demografico_data['por_grupo_etario']['distribucion']
            df_edad = pd.DataFrame(distribucion_edad.items(), columns=['grupo_etario', 'cantidad'])
        else:
            return None
    else:
        # Usar la distribución por delito específico (cantidad de cruce)
        if 'delitos_por_grupo_etario' not in demografico_data:
            return None
            
        data_por_grupo_etario = demografico_data['delitos_por_grupo_etario']
        
        # CORRECCIÓN DE LÓGICA: Extrae la cantidad del delito para CADA Grupo Etario.
        distribucion_edad_delito = {
            grupo: data_por_grupo_etario[grupo].get(filtro_delito, 0)
            for grupo in data_por_grupo_etario.keys()
        }
        
        # Filtramos grupos con cantidad > 0 para la visualización
        distribucion_edad_delito = {k: v for k, v in distribucion_edad_delito.items() if v > 0}
        
        if not distribucion_edad_delito:
             # Retorna None si no hay datos para ese delito específico en el cruce por edad
             return None 
             
        df_edad = pd.DataFrame(distribucion_edad_delito.items(), columns=['grupo_etario', 'cantidad'])


    df_edad['cantidad'] = df_edad['cantidad'].astype(int)
    
    titulo_grafico = f'Eventos por Grupo Etario: **{filtro_delito}**'

    fig_edad = px.bar(df_edad, x='grupo_etario', y='cantidad', 
                      title=titulo_grafico,
                      labels={'grupo_etario': 'Grupo Etario', 'cantidad': 'Cantidad de Eventos'},
                      color='grupo_etario', 
                      color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_edad.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    return fig_edad
    
# NOTA: plot_temporal_eventos ha sido eliminada.


# ------------------------------------------------------------------------------
# 3. Configuración y Layout Principal
# ------------------------------------------------------------------------------

st.set_page_config(
    page_title="Visor Analítico – CrimeLab",
    page_icon="🗺️",
    layout="wide"
)

# Aplicar estilos y menú
inject_styles()
draw_sidebar_menu()

st.title("🗺️ Visor Analítico de Seguridad Ciudadana")

# Definir Pestañas (UNIFICADAS)
tab_historicos, tab_predictivo = st.tabs(["📊 Históricos y Descriptivos", "🔮 Proyecciones"])

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
# PESTAÑA 1: HISTÓRICOS Y DESCRIPTIVOS (REORDENADA)
# ------------------------------------------------------------------------------
with tab_historicos:
    st.header("Análisis Histórico y Descriptivo de Seguridad Ciudadana")
    
    st.markdown("---") 

    # ==========================================================================
    # === SECCIÓN 1.1: PERFILES Y FACTORES CONTEXTUALES (MODELO EVENT)
    # ==========================================================================
    with st.container(border=True):
        st.subheader("Perfiles y Factores Contextuales")
        st.markdown("Análisis enfocado en la naturaleza de los eventos, perfiles involucrados y factores temporales/demográficos.")

        # === 1. Indicadores Globales Event ===
        st.subheader("📊 Resumen General")
        col1, col2, col3, col4 = st.columns(4)
        
        periodo_event = f"{resumen_event['periodo']['anio_inicio']} - {resumen_event['periodo']['anio_fin']}"
        
        col1.metric("Total de Eventos", f"{resumen_event['total_eventos']:,}")
        col2.metric("Período Analizado", periodo_event)
        col3.metric("Municipios Cubiertos", f"{resumen_event['geografia']['n_municipios']}")
        col4.metric("Delito más Reportado", delito_mas_comun_event) 
        
        st.markdown("---")

        # === 2. Análisis Demográfico (Grupo Etario) - AHORA PRIMERO (FILTRO CORREGIDO) ===
        st.subheader("👨‍👩‍👧‍👦 Análisis Demográfico por Grupo Etario")
        
        # Selector de filtro por delito
        opciones_delito_demo = ["Delitos Totales"] + listado_delitos
        filtro_delito_demo = st.selectbox("Filtrar Análisis Demográfico por Delito:", opciones_delito_demo, key="filtro_delito_demo")

        # Usa la función corregida
        fig_edad = plot_demografico_etario(demografico_event, demografico_event, filtro_delito_demo)
        
        if fig_edad:
            st.plotly_chart(fig_edad, use_container_width=True)
        else:
            st.info(f"No hay datos disponibles para el análisis demográfico o el delito: **{filtro_delito_demo}**.")

        st.markdown("---")
        
        # === 3. Distribución de Delitos y Perfiles ===
        st.subheader("Distribuciones Clave")
        col_delito, col_perfil = st.columns(2)
        
        with col_delito:
            fig_delito = plot_distribucion_event_delitos(distribucion_delitos_event)
            if fig_delito:
                st.plotly_chart(fig_delito, use_container_width=True)
            else:
                st.info("No hay datos de distribución de delitos por evento.")
                
        with col_perfil:
            # Selector de filtro por delito para Perfiles (LÓGICA CORRECTA)
            opciones_delito_perfil = ["Delitos Totales"] + listado_delitos
            filtro_delito_perfil = st.selectbox("Filtrar Distribución de Perfiles por Delito:", opciones_delito_perfil, key="filtro_delito_perfil")

            # Usa la función plot_perfiles (correcta) con el filtro
            fig_perfil = plot_perfiles(distribucion_perfiles_event, cruces_delito_perfil_event, filtro_delito_perfil)
            if fig_perfil:
                st.plotly_chart(fig_perfil, use_container_width=True)
            else:
                st.info(f"No hay datos de distribución de perfiles o el delito: **{filtro_delito_perfil}**.")
                
        # === 4. Análisis Temporal (Mensual) - SECCIÓN ELIMINADA ===
        # La sección de Variación Temporal fue eliminada según la solicitud.


    st.markdown("""<hr style="height:5px;border:none;color:#333;background-color:#333;" />""", unsafe_allow_html=True)
    
    # ==========================================================================
    # === SECCIÓN 1.2: RIESGO Y TENDENCIA (MODELO DOMINANTE)
    # ==========================================================================
    with st.container(border=True):
        st.subheader("Riesgo y Tendencia")
        st.markdown("Métricas enfocadas en la clasificación de riesgo municipal y la tendencia de los delitos dominantes.")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Delito más frecuente", stats["delito_mas_frecuente"]["nombre"], delta=f"{stats['delito_mas_frecuente']['porcentaje']:.1f}% del total")
        col2.metric("Arma más frecuente", stats["arma_mas_frecuente"]["nombre"], delta=f"{stats['arma_mas_frecuente']['porcentaje']:.1f}% del total")
        col3.metric("Total delitos dominantes", f"{stats['suma_delitos_dominantes']:,}")
        
        cambio_vs_anterior = tendencias_raw['cambio_porcentual'].get(str(stats['periodo']['fin'] - 1), 0)
        col4.metric("Tendencia General", tendencias_raw['tendencia_general'].capitalize(), delta=f"Cambio vs año anterior: {cambio_vs_anterior:.1f}%")

        st.markdown("---")
        
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

        st.subheader("Distribución Global de Delitos")
        fig_distribucion = plot_distribucion_delitos(stats)
        
        if fig_distribucion:
            st.plotly_chart(fig_distribucion, use_container_width=True)
        else:
            st.info("La distribución global de delitos no está disponible.")
        
        st.markdown("---")

        st.header("⏳ Análisis de Tendencia Anual (Histórica y Proyectada)")
        
        with st.container(border=True): 
            st.subheader("🎛️ Controles de Exploración")
            col_anho, col_vacio = st.columns([1, 3])

            años_disponibles = sorted(list(set(range(2010, 2026)))) 
            año_selected = col_anho.selectbox("Año de Referencia:", años_disponibles, index=len(años_disponibles)-1, key="anio_desc")
            
        fig_tendencia = plot_tendencia_anual(tendencias_raw, año_selected)
        st.plotly_chart(fig_tendencia, use_container_width=True)

        st.markdown("---")

        st.header("🏅 Ranking de Criminalidad Municipal")
        
        col_rank_settings, col_rank_table = st.columns([1, 3])
        with col_rank_settings:
            top_n = st.slider("Mostrar TOP N municipios", 5, 30, 10, key="top_n_desc")
        with col_rank_table:
            df_top = df_mun.head(top_n).set_index("Ranking")
            st.dataframe(df_top, use_container_width=True)


# ------------------------------------------------------------------------------
# PESTAÑA 2: PROYECCIONES (MODELO SELECTOR)
# ------------------------------------------------------------------------------
with tab_predictivo:
    
    # Layout con selector a la derecha
    col_controls, col_selector = st.columns([3, 1])

    with col_selector:
        st.markdown("#### Selección de Modelos")
        st.markdown("---")
        # Checkboxes para la selección de modelos
        modelo_dominante_selected = st.checkbox("Dominante: Delito/Arma", value=True, key="chk_dominante")
        modelo_eventos_selected = st.checkbox("Eventos: Perfil/Contexto", value=False, key="chk_eventos", disabled=True)
        st.info("Solo el modelo **Dominante** está implementado para predicción por ahora.")

    with col_controls:
        st.header("🔮 Proyección y Simulación de Riesgo")
        
        if not modelo_dominante_selected:
            st.warning("Selecciona el modelo **Dominante** en el panel derecho para activar las predicciones.")
        elif modelos_predictivos is None:
            st.warning("⚠️ **ATENCIÓN:** La predicción está deshabilitada porque los archivos `.joblib` no pudieron ser cargados correctamente.")
        else:
            # El contenido de predicción solo se muestra si el modelo Dominante está seleccionado.
            with st.container(border=True):
                st.subheader("📅 Controles de Predicción")
                col_mun, col_mes, col_anio, col_btn = st.columns([2, 1, 1, 1])
                
                municipios_predict = sorted(list(municipio_name_map.values()))
                municipio_pred_name = col_mun.selectbox("Selecciona un municipio para predecir:", municipios_predict, key="mun_pred")
                
                codigo_municipio_pred = next((k for k, v in municipio_name_map.items() if v == municipio_pred_name), None)

                today = datetime.date.today()
                # Calcula el próximo mes
                next_month = today.month % 12 + 1
                next_year = today.year + (1 if today.month == 12 else 0)
                
                meses_disp = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                              7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

                mes_pred = col_mes.number_input(f"Mes ({meses_disp.get(next_month)})", min_value=1, max_value=12, value=next_month, key="mes_pred")
                anio_pred = col_anio.number_input("Año", min_value=today.year, max_value=today.year + 10, value=next_year, key="anio_pred")

                if col_btn.button("Ejecutar Predicción 🚀"):
                    if codigo_municipio_pred and codigo_municipio_pred in mun_resumen:
                        with st.spinner(f"Calculando predicción para **{municipio_pred_name}** en **{meses_disp.get(mes_pred)}/{anio_pred}**..."):
                            resultado = predecir_delito_arma(str(codigo_municipio_pred), int(anio_pred), int(mes_pred), modelos_predictivos)
                            st.session_state["prediccion_actual"] = resultado
                    else:
                        st.error("Selecciona un municipio válido o uno con datos descriptivos.")

            st.markdown("---")

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