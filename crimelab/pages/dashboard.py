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

# Get the base directory (crimelab folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_file_path(base_dir, *relative_path_components):
    """Generates a normalized path for any operating system."""
    return os.path.normpath(os.path.join(base_dir, *relative_path_components))


# ============================
# DATA LOADING FUNCTIONS
# ============================

@st.cache_resource(show_spinner="Cargando modelo de regresión mensual...")
def load_regression_monthly():
    """Load the monthly regression model and its components."""
    import joblib
    modelos = {}
    try:
        model_path = get_file_path(BASE_DIR, "..", "models", "predictivos", "regression_monthly", "xgb_regressor.joblib")
        scaler_path = get_file_path(BASE_DIR, "..", "models", "predictivos", "regression_monthly", "scaler.joblib")
        metadata_path = get_file_path(BASE_DIR, "..", "models", "predictivos", "regression_monthly", "metadata.json")
        
        modelos["model"] = joblib.load(model_path)
        modelos["scaler"] = joblib.load(scaler_path)
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            modelos["metadata"] = json.load(f)
        
        return modelos
    except FileNotFoundError as e:
        return None
    except Exception as e:
        return None


@st.cache_resource(show_spinner="Cargando modelo de regresión anual...")
def load_regression_annual():
    """Load the annual regression model and its components."""
    import joblib
    import glob
    modelos = {}
    try:
        annual_dir = get_file_path(BASE_DIR, "..", "models", "regression", "annual")
        
        # Find the most recent model files
        model_files = glob.glob(os.path.join(annual_dir, "regression_annual_randomforest_*.joblib"))
        scaler_files = glob.glob(os.path.join(annual_dir, "scaler_*.joblib"))
        metadata_files = glob.glob(os.path.join(annual_dir, "regression_annual_metadata_*.json"))
        
        if not model_files or not scaler_files or not metadata_files:
            return None
        
        # Use the most recent (sorted by name which includes timestamp)
        model_path = sorted(model_files)[-1]
        scaler_path = sorted(scaler_files)[-1]
        metadata_path = sorted(metadata_files)[-1]
        
        modelos["model"] = joblib.load(model_path)
        modelos["scaler"] = joblib.load(scaler_path)
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            modelos["metadata"] = json.load(f)
        
        return modelos
    except FileNotFoundError as e:
        return None
    except Exception as e:
        return None


@st.cache_data(show_spinner="Cargando datos descriptivos y geográficos...")
def load_descriptive_data():
    """Load all JSON, GeoJSON files and necessary mappings."""
    data_dominant, data_event = {}, {}
    geojson_data = {}
    municipio_name_map = {}
    
    dominant_dir = get_file_path(BASE_DIR, ".." ,"models", "descriptivo", "classification_dominant")
    event_dir = get_file_path(BASE_DIR, ".." ,"models", "descriptivo", "classification_event")
    geojson_path = get_file_path(BASE_DIR, ".." ,"data", "silver", "dane_geo", "geografia_silver.geojson")
    
    files_to_load = {
        "stats_dom": get_file_path(dominant_dir, "estadisticas_generales.json"),
        "mun_resumen_dom": get_file_path(dominant_dir, "municipios_resumen.json"),
        "tendencias_dom": get_file_path(dominant_dir, "tendencias_anuales.json"),
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
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        for key, path in files_to_load.items():
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
                
                if key.endswith("_dom"):
                    data_dominant[key.replace("_dom", "")] = content
                elif key.endswith("_event"):
                    data_event[key.replace("_event", "")] = content

        for feature in geojson_data.get("features", []):
            codigo = str(feature["properties"].get("codigo_municipio"))
            nombre = feature["properties"].get("municipio")
            if codigo and nombre:
                municipio_name_map[codigo] = nombre.upper()

        return data_dominant, data_event, geojson_data, municipio_name_map

    except FileNotFoundError as e:
        st.error(f"Error al cargar archivos descriptivos/geográficos: Revise las rutas. Detalles: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Error inesperado durante la carga de datos descriptivos. Detalles: {e}")
        st.stop()


# ============================
# VISUALIZATION FUNCTIONS
# ============================

COLOR_RIESGO = {"Alto": "#e74c3c", "Medio-Alto": "#e67e22", "Medio-Bajo": "#f1c40f", "Bajo": "#2ecc71"}

def get_color(riesgo):
    return COLOR_RIESGO.get(riesgo, "#bdc3c7")


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
    if "distribucion_delitos" not in stats_data or not stats_data["distribucion_delitos"]: 
        return None
        
    delitos_data = {
        delito: data.get("porcentaje", 0) 
        for delito, data in stats_data["distribucion_delitos"].items()
    }

    df_dist = pd.DataFrame(list(delitos_data.items()), columns=['Delito', 'Porcentaje'])
    df_dist['Porcentaje'] = df_dist['Porcentaje'].astype(float) 
    
    if df_dist['Porcentaje'].sum() > 100 or df_dist['Porcentaje'].sum() < 90:
        df_dist['Porcentaje'] = df_dist['Porcentaje'] / df_dist['Porcentaje'].sum()
    
    fig = px.pie(df_dist, values='Porcentaje', names='Delito', title='Distribución Global de Delitos Dominantes en Santander', hole=0.4)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title_font=dict(size=22, family="Arial", color="#333"), uniformtext_minsize=12, uniformtext_mode='hide', legend_title_text='Tipos de Delito')
    return fig


def predecir_regression_monthly(codigo_municipio, anio, mes, modelos, mun_resumen):
    """Execute the monthly regression model prediction."""
    if modelos is None or "model" not in modelos:
        return {"error": "Modelo de regresión mensual no cargado correctamente."}

    model = modelos["model"]
    scaler = modelos["scaler"]
    
    if codigo_municipio not in mun_resumen:
        return {"error": "Municipio no encontrado en el resumen descriptivo."}

    # Base historical data for the municipality
    base_count = mun_resumen[codigo_municipio]["total_delitos"] / 12  # Monthly average
    
    # Calculate calendar features
    import calendar
    _, days_in_month = calendar.monthrange(anio, mes)
    
    # Estimate working days and weekends
    first_day = datetime.date(anio, mes, 1)
    weekdays = sum(1 for day in range(1, days_in_month + 1) 
                   if datetime.date(anio, mes, day).weekday() < 5)
    weekends = days_in_month - weekdays
    
    # Colombian holidays approximation (rough estimate)
    festivos = 1 if mes in [1, 3, 4, 5, 6, 7, 8, 10, 11, 12] else 0
    
    # Simulated demographic/geographic features based on municipality data
    poblacion_base = base_count * 1000  # Rough estimation
    area_km2 = 500  # Default area
    
    features = {
        'anio': anio,
        'mes': mes,
        'trimestre': (mes - 1) // 3 + 1,
        'mes_sin': np.sin(2 * np.pi * mes / 12),
        'mes_cos': np.cos(2 * np.pi * mes / 12),
        'n_dias_laborales': weekdays,
        'n_fines_de_semana': weekends,
        'n_festivos': festivos,
        'es_fin_ano': 1 if mes == 12 else 0,
        'codigo_municipio': int(codigo_municipio),
        'area_km2': area_km2,
        'densidad_poblacional': poblacion_base / area_km2,
        'n_centros_poblados': 5,
        'poblacion_total': poblacion_base,
        'proporcion_menores': 0.25,
        'proporcion_adultos': 0.60,
        'proporcion_adolescentes': 0.15,
        'lag_1': base_count * np.random.uniform(0.9, 1.1),
        'lag_3': base_count * np.random.uniform(0.85, 1.15),
        'lag_12': base_count * np.random.uniform(0.8, 1.2),
        'roll_mean_3': base_count,
        'roll_mean_12': base_count,
        'roll_std_3': base_count * 0.1,
        'roll_std_12': base_count * 0.15,
        'pct_change_1': np.random.uniform(-0.1, 0.1),
        'pct_change_3': np.random.uniform(-0.15, 0.15),
        'pct_change_12': np.random.uniform(-0.2, 0.2),
    }
    
    X = pd.DataFrame([features])
    
    try:
        feature_order = scaler.feature_names_in_.tolist()
        X = X[feature_order]
        X_scaled = scaler.transform(X)
        prediccion = model.predict(X_scaled)[0]
        
        return {
            "total_delitos_predicho": max(0, round(prediccion)),
            "mes": mes,
            "anio": anio
        }
    except Exception as e:
        return {"error": f"Error durante la predicción: {e}"}


def predecir_regression_annual(codigo_municipio, anio, modelos, mun_resumen):
    """Execute the annual regression model prediction."""
    if modelos is None or "model" not in modelos:
        return {"error": "Modelo de regresión anual no cargado correctamente."}

    model = modelos["model"]
    scaler = modelos["scaler"]
    
    if codigo_municipio not in mun_resumen:
        return {"error": "Municipio no encontrado en el resumen descriptivo."}

    # Base historical data for the municipality
    base_count = mun_resumen[codigo_municipio]["total_delitos"]
    poblacion_base = base_count * 100  # Rough estimation
    
    # Simulated features for annual prediction
    features = {
        'poblacion_total': poblacion_base,
        'poblacion_menores': poblacion_base * 0.25,
        'poblacion_adultos': poblacion_base * 0.60,
        'poblacion_adolescentes': poblacion_base * 0.15,
        'area_km2': 500,
        'densidad_poblacional': poblacion_base / 500,
        'centros_por_km2': 0.01,
        'ABIGEATO': base_count * 0.02,
        'HURTOS': base_count * 0.30,
        'LESIONES': base_count * 0.25,
        'VIOLENCIA INTRAFAMILIAR': base_count * 0.20,
        'AMENAZAS': base_count * 0.08,
        'DELITOS SEXUALES': base_count * 0.05,
        'EXTORSION': base_count * 0.02,
        'HOMICIDIOS': base_count * 0.03,
        'es_post_2020': 1 if anio > 2020 else 0,
        'total_delitos_lag1': base_count * np.random.uniform(0.9, 1.1),
        'total_delitos_lag2': base_count * np.random.uniform(0.85, 1.15),
        'delitos_media_movil_3': base_count,
    }
    
    X = pd.DataFrame([features])
    
    try:
        feature_order = scaler.feature_names_in_.tolist()
        X = X[feature_order]
        X_scaled = scaler.transform(X)
        prediccion = model.predict(X_scaled)[0]
        
        return {
            "total_delitos_predicho": max(0, round(prediccion)),
            "anio": anio
        }
    except Exception as e:
        return {"error": f"Error durante la predicción: {e}"}


def plot_distribucion_event_delitos(data):
    """Bar chart for crime distribution from Event Model."""
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
    """Horizontal bar chart for profile distribution (Aggressor/Victim)."""
    
    def agrupar_perfil(perfil):
        perfil = str(perfil).upper().strip()
        if 'NO REPORTADO' in perfil or 'NO REPORTA' in perfil or 'NAN' in perfil or 'NONE' in perfil:
            return 'NO REPORTADO/NO ESPECIFICADO'
        return perfil
        
    if filtro_delito == "Delitos Totales":
        if 'distribucion' not in data_global or not data_global['distribucion']:
            return None
        df = pd.DataFrame(data_global['distribucion'])
        df['porcentaje'] = df['porcentaje'].astype(float)
        df['valor'] = df['porcentaje']
    else:
        if 'cruce_porcentual' not in cruces_data or filtro_delito not in cruces_data['cruce_porcentual']:
            return None
        
        perfiles_porcentaje = cruces_data['cruce_porcentual'][filtro_delito]
        df = pd.DataFrame(perfiles_porcentaje.items(), columns=['perfil', 'porcentaje'])
        df['valor'] = df['porcentaje'].astype(float)
        
    df['perfil_agrupado'] = df['perfil'].apply(agrupar_perfil)
    
    df_grouped = df.groupby('perfil_agrupado').agg(
        valor=('valor', 'sum')
    ).reset_index()

    df_grouped['porcentaje'] = df_grouped['valor']
    df_grouped['porcentaje_label'] = df_grouped['porcentaje'].round(1).astype(str) + '%'
    df_grouped = df_grouped.sort_values(by='porcentaje', ascending=True)

    titulo_grafico = f'Distribución de Perfiles Agrupados: {filtro_delito.upper()}'
    
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
    """Bar chart for age group distribution."""
    
    if filtro_delito == "Delitos Totales":
        if demografico_data and 'por_grupo_etario' in demografico_data and 'distribucion' in demografico_data['por_grupo_etario']:
            distribucion_edad = demografico_data['por_grupo_etario']['distribucion']
            df_edad = pd.DataFrame(distribucion_edad.items(), columns=['grupo_etario', 'cantidad'])
        else:
            return None
    else:
        if 'delitos_por_grupo_etario' not in demografico_data:
            return None
            
        data_por_grupo_etario = demografico_data['delitos_por_grupo_etario']
        
        distribucion_edad_delito = {
            grupo: data_por_grupo_etario[grupo].get(filtro_delito, 0)
            for grupo in data_por_grupo_etario.keys()
        }
        
        distribucion_edad_delito = {k: v for k, v in distribucion_edad_delito.items() if v > 0}
        
        if not distribucion_edad_delito:
             return None 
             
        df_edad = pd.DataFrame(distribucion_edad_delito.items(), columns=['grupo_etario', 'cantidad'])

    df_edad['cantidad'] = df_edad['cantidad'].astype(int)
    
    titulo_grafico = f'Eventos por Grupo Etario: {filtro_delito.upper()}'

    fig_edad = px.bar(df_edad, x='grupo_etario', y='cantidad', 
                      title=titulo_grafico,
                      labels={'grupo_etario': 'Grupo Etario', 'cantidad': 'Cantidad de Eventos'},
                      color='grupo_etario', 
                      color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_edad.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    return fig_edad


# ============================
# MAIN RENDER FUNCTION
# ============================

def render():
    """Render the dashboard page."""
    
    # Load data and models
    data_load_result = load_descriptive_data()
    data_dominant, data_event, geojson_data, municipio_name_map = data_load_result

    # Assign for DOMINANT model
    stats = data_dominant["stats"]
    mun_resumen = data_dominant["mun_resumen"]
    tendencias_raw = data_dominant["tendencias"]

    # Assign for EVENT model
    resumen_event = data_event["resumen"] 
    distribucion_delitos_event = data_event["distribucion_delitos"]
    distribucion_perfiles_event = data_event["distribucion_perfiles"]
    demografico_event = data_event["demografico"] 
    cruces_delito_perfil_event = data_event["cruces_delito_perfil"]

    delito_mas_comun_event = distribucion_delitos_event["delito_mas_comun"]["nombre"]

    if "tipos_delito" in resumen_event and "tipos" in resumen_event["tipos_delito"]:
        listado_delitos = sorted(resumen_event["tipos_delito"]["tipos"])
    else:
        try:
            listado_delitos = sorted(list(distribucion_delitos_event["distribucion_delitos"].keys()))
        except:
            listado_delitos = []

    st.title("🗺️ Visor Analítico de Seguridad Ciudadana")

    # Define Tabs
    tab_historicos, tab_predictivo = st.tabs(["📊 Históricos y Descriptivos", "🔮 Proyecciones"])

    # Generate municipality DataFrame
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
    # TAB 1: HISTORICAL AND DESCRIPTIVE
    # ------------------------------------------------------------------------------
    with tab_historicos:
        st.header("Análisis Histórico y Descriptivo de Seguridad Ciudadana")
        st.markdown("---") 

        # SECTION 1.1: PROFILES AND CONTEXTUAL FACTORS (EVENT MODEL)
        with st.container(border=True):
            st.subheader("Perfiles y Factores Contextuales")
            st.markdown("Análisis enfocado en la naturaleza de los eventos, perfiles involucrados y factores temporales/demográficos.")

            st.subheader("Resumen General")
            col1, col2, col3, col4 = st.columns(4)
            
            periodo_event = f"{resumen_event['periodo']['anio_inicio']} - {resumen_event['periodo']['anio_fin']}"
            
            col1.metric("Total de Eventos", f"{resumen_event['total_eventos']:,}")
            col2.metric("Período Analizado", periodo_event)
            col3.metric("Municipios Cubiertos", f"{resumen_event['geografia']['n_municipios']}")
            col4.metric("Delito más Reportado", delito_mas_comun_event) 
            
            st.markdown("---")

            st.subheader("Análisis Demográfico por Grupo Etario")
            
            opciones_delito_demo = ["Delitos Totales"] + listado_delitos
            filtro_delito_demo = st.selectbox("Filtrar Análisis Demográfico por Delito:", opciones_delito_demo, key="filtro_delito_demo")

            fig_edad = plot_demografico_etario(demografico_event, demografico_event, filtro_delito_demo)
            
            if fig_edad:
                st.plotly_chart(fig_edad, use_container_width=True)
            else:
                st.info(f"No hay datos disponibles para el análisis demográfico o el delito: {filtro_delito_demo.upper()}.")

            st.markdown("---")
            
            st.subheader("Distribuciones Clave")
            col_delito, col_perfil = st.columns(2)
            
            with col_delito:
                fig_delito = plot_distribucion_event_delitos(distribucion_delitos_event)
                if fig_delito:
                    st.plotly_chart(fig_delito, use_container_width=True)
                else:
                    st.info("No hay datos de distribución de delitos por evento.")
                    
            with col_perfil:
                opciones_delito_perfil = ["Delitos Totales"] + listado_delitos
                filtro_delito_perfil = st.selectbox("Filtrar Distribución de Perfiles por Delito:", opciones_delito_perfil, key="filtro_delito_perfil")

                fig_perfil = plot_perfiles(distribucion_perfiles_event, cruces_delito_perfil_event, filtro_delito_perfil)
                if fig_perfil:
                    st.plotly_chart(fig_perfil, use_container_width=True)
                else:
                    st.info(f"No hay datos de distribución de perfiles o el delito: {filtro_delito_perfil.upper()}.")

        st.markdown("""<hr style="height:5px;border:none;color:#333;background-color:#333;" />""", unsafe_allow_html=True)
        
        # SECTION 1.2: RISK AND TREND (DOMINANT MODEL)
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
            
            st.header("Mapa de Clasificación de Riesgo - Santander")
            
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

            st.header("Análisis de Tendencia Anual (Histórica y Proyectada)")
            
            with st.container(border=True): 
                st.subheader("Controles de Exploración")
                col_anho, col_vacio = st.columns([1, 3])

                años_disponibles = sorted(list(set(range(2010, 2026)))) 
                año_selected = col_anho.selectbox("Año de Referencia:", años_disponibles, index=len(años_disponibles)-1, key="anio_desc")
                
            fig_tendencia = plot_tendencia_anual(tendencias_raw, año_selected)
            st.plotly_chart(fig_tendencia, use_container_width=True)

            st.markdown("---")

            st.header("Ranking de Criminalidad Municipal")
            
            col_rank_settings, col_rank_table = st.columns([1, 3])
            with col_rank_settings:
                top_n = st.slider("Mostrar TOP N municipios", 5, 30, 10, key="top_n_desc")
            with col_rank_table:
                df_top = df_mun.head(top_n).set_index("Ranking")
                st.dataframe(df_top, use_container_width=True)

    # ------------------------------------------------------------------------------
    # TAB 2: PREDICTIONS
    # ------------------------------------------------------------------------------
    with tab_predictivo:
        # Load all models
        modelos_regression_monthly = load_regression_monthly()
        modelos_regression_annual = load_regression_annual()
        
        st.header("Proyección y Simulación de Riesgo")
        
        # Model options (define before checking availability)
        MODELOS_OPCIONES = {
            "Regresión: Delitos Mensuales": {"key": "regression_monthly", "tipo": "regresion"},
            "Regresión: Delitos Anuales": {"key": "regression_annual", "tipo": "regresion"},
        }
        
        col_controls, col_selector = st.columns([3, 1])

        with col_selector:
            modelo_seleccionado = st.selectbox(
                "Modelo predictivo:",
                options=list(MODELOS_OPCIONES.keys()),
                index=0,
                key="modelo_pred_select",
                help="Selecciona el modelo de predicción a utilizar"
            )
            
            modelo_info = MODELOS_OPCIONES[modelo_seleccionado]
            modelo_key = modelo_info["key"]
            
            # Check model availability
            modelo_disponible = False
            if modelo_key == "regression_monthly" and modelos_regression_monthly is not None:
                modelo_disponible = True
            elif modelo_key == "regression_annual" and modelos_regression_annual is not None:
                modelo_disponible = True
            
            if not modelo_disponible:
                st.warning(f"El modelo no pudo ser cargado. Verifique los archivos.")

        with col_controls:
            if not modelo_disponible:
                st.warning("⚠️ **ATENCIÓN:** La predicción está deshabilitada porque los archivos del modelo no pudieron ser cargados correctamente.")
            else:
                municipios_predict = sorted(list(municipio_name_map.values()))
                today = datetime.date.today()
                next_month = today.month % 12 + 1
                next_year = today.year + (1 if today.month == 12 else 0)
                
                meses_disp = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                              7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
                
                # Different layouts based on model type
                if modelo_key == "regression_annual":
                    # Annual model: Municipality + Year only
                    col_mun, col_anio, col_empty, col_btn = st.columns([2, 1, 1, 1])
                    
                    municipio_pred_name = col_mun.selectbox("Selecciona un municipio para predecir:", municipios_predict, key="mun_pred")
                    codigo_municipio_pred = next((k for k, v in municipio_name_map.items() if v == municipio_pred_name), None)
                    
                    anio_pred = col_anio.number_input("Año", min_value=today.year, max_value=today.year + 10, value=next_year, key="anio_pred")
                    mes_pred = None  # Not used for annual model
                    
                else:
                    # Monthly Regression: Municipality + Month + Year
                    col_mun, col_mes, col_anio, col_btn = st.columns([2, 1, 1, 1])
                    
                    municipio_pred_name = col_mun.selectbox("Selecciona un municipio para predecir:", municipios_predict, key="mun_pred")
                    codigo_municipio_pred = next((k for k, v in municipio_name_map.items() if v == municipio_pred_name), None)
                    
                    mes_pred = col_mes.number_input(f"Mes ({meses_disp.get(next_month)})", min_value=1, max_value=12, value=next_month, key="mes_pred")
                    anio_pred = col_anio.number_input("Año", min_value=today.year, max_value=today.year + 10, value=next_year, key="anio_pred")

                if col_btn.button("Ejecutar Predicción 🚀"):
                    if codigo_municipio_pred and codigo_municipio_pred in mun_resumen:
                        if modelo_key == "regression_annual":
                            with st.spinner(f"Calculando predicción para {municipio_pred_name.upper()} en {anio_pred}..."):
                                resultado = predecir_regression_annual(str(codigo_municipio_pred), int(anio_pred), modelos_regression_annual, mun_resumen)
                                resultado["modelo"] = modelo_key
                                st.session_state["prediccion_actual"] = resultado
                        else:  # regression_monthly
                            with st.spinner(f"Calculando predicción para {municipio_pred_name.upper()} en {meses_disp.get(mes_pred)}/{anio_pred}..."):
                                resultado = predecir_regression_monthly(str(codigo_municipio_pred), int(anio_pred), int(mes_pred), modelos_regression_monthly, mun_resumen)
                                resultado["modelo"] = modelo_key
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
                        pred_modelo = pred.get("modelo", "regression_monthly")
                        
                        if pred_modelo == "regression_monthly":
                            # Monthly regression result
                            st.success(f"Predicción exitosa para {municipio_pred_name.upper()} en {meses_disp.get(pred['mes'])}/{pred['anio']}:")
                            
                            col_total, col_desc = st.columns([1, 2])
                            
                            col_total.metric("Total Delitos Predichos", f"{pred['total_delitos_predicho']:,}")
                            
                            mun_info = mun_resumen.get(codigo_municipio_pred, {})
                            riesgo = mun_info.get("categoria_riesgo", "N/A")
                            promedio_mensual = mun_info.get("total_delitos", 0) / 12
                            
                            col_desc.info(f"""
                            CONTEXTO HISTÓRICO:
                            • Categoría de Riesgo: {riesgo.upper() if riesgo != "N/A" else riesgo}
                            • Promedio Mensual Histórico: ~{promedio_mensual:.0f} delitos
                            • Predicción vs Promedio: {((pred['total_delitos_predicho'] / promedio_mensual - 1) * 100):+.1f}%
                            """)
                            
                        elif pred_modelo == "regression_annual":
                            # Annual regression result
                            st.success(f"Predicción exitosa para {municipio_pred_name.upper()} en el año {pred['anio']}:")
                            
                            col_total, col_desc = st.columns([1, 2])
                            
                            col_total.metric("Total Delitos Anuales Predichos", f"{pred['total_delitos_predicho']:,}")
                            
                            mun_info = mun_resumen.get(codigo_municipio_pred, {})
                            riesgo = mun_info.get("categoria_riesgo", "N/A")
                            total_historico = mun_info.get("total_delitos", 0)
                            
                            col_desc.info(f"""
                            CONTEXTO HISTÓRICO:
                            • Categoría de Riesgo: {riesgo.upper() if riesgo != "N/A" else riesgo}
                            • Total Histórico Registrado: {total_historico:,} delitos
                            • Predicción vs Histórico: {((pred['total_delitos_predicho'] / total_historico - 1) * 100) if total_historico > 0 else 0:+.1f}%
                            """)

                else:
                    st.info("Utiliza los controles de predicción de arriba para obtener el resultado del modelo predictivo.")
