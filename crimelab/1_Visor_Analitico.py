import streamlit as st
import json
import os

import streamlit as st
import pandas as pd
import plotly.express as px

# Cargar archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Configuracion inicial 
st.set_page_config(
    page_title="Visor Analítico – CrimeLab",
    page_icon="🗺️",
    layout="wide"
)

# ============================
# Título
# ============================
st.title("🗺️ Visor Analítico")

# ============================
# Indicadores Generales
# Usamos estadisticas_generales.json (ruta: models/descriptivo/classification_dominant/estadisticas_generales.json) para mostrar algunos indicadores generales
# ============================

# Ruta *multiplataforma* al archivo JSON
ruta_json = os.path.join(
    BASE_DIR,
    "..",  # Subir un nivel porque tu .py está dentro de /crimelab
    "models",
    "descriptivo",
    "classification_dominant",
    "estadisticas_generales.json"
)

# Normaliza la ruta (convierte .. y separadores según SO)
ruta_json = os.path.normpath(ruta_json)

# Cargar JSON
with open(ruta_json, "r", encoding="utf-8") as f:
    stats = json.load(f)

print("Archivo cargado desde:", ruta_json)

st.header("📊 Indicadores Generales de Santander")

col1, col2, col3 = st.columns(3)

col1.metric("Delito más frecuente", stats["delito_mas_frecuente"]["nombre"])
col2.metric("Arma más frecuente", stats["arma_mas_frecuente"]["nombre"])
col3.metric("Total delitos dominantes", stats["suma_delitos_dominantes"])

# ============================
# Tendencias Anuales
# Usamos tendencias_anuales.json (ruta: models/descriptivo/classification_dominant/tendencias_anuales.json) para mostrar tendencias anuales
# ============================

# Ruta *multiplataforma* al archivo JSON
ruta_json = os.path.join(
    BASE_DIR,
    "..",   # subir un nivel (tu script está dentro de /crimelab)
    "models",
    "descriptivo",
    "classification_dominant",
    "tendencias_anuales.json"
)

# Normaliza la ruta
ruta_json = os.path.normpath(ruta_json)

# Cargar el JSON
with open(ruta_json, "r", encoding="utf-8") as f:
    tendencias = json.load(f)


# Crear DataFrame con nombres más claros
df_tend = pd.DataFrame({
    "Año": list(tendencias["delitos_por_anio"].keys()),
    "Delitos": list(tendencias["delitos_por_anio"].values())
})

# Asegurar que Año sea numérico para ordenar correctamente
df_tend["Año"] = df_tend["Año"].astype(int)

# Gráfica mejorada
fig = px.line(
    df_tend,
    x="Año",
    y="Delitos",
    title="Tendencia Histórica de Delitos",
    markers=True  # puntos visibles
)

# Personalizar apariencia profesional
fig.update_traces(
    line=dict(width=3, color="#1f77b4"),
    marker=dict(size=6)
)

fig.update_layout(
    title_font=dict(size=24, family="Arial", color="#333"),
    xaxis_title="Año",
    yaxis_title="Número de Delitos",
    xaxis=dict(showgrid=True, gridcolor="rgba(200,200,200,0.3)"),
    yaxis=dict(
        showgrid=True,
        gridcolor="rgba(200,200,200,0.3)",
        tickformat=",",       # separador de miles
    ),
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)

print("Archivo cargado desde:", ruta_json)

# ============================
# Estacionalidad Mensual
# Usamos la misma fuente de tendencias_anuales.json
# ============================

# Crear DataFrame más claro y profesional
df_est = pd.DataFrame({
    "Mes": list(tendencias["estacionalidad_mensual"].keys()),
    "Porcentaje (%)": list(tendencias["estacionalidad_mensual"].values())
})

# Ordenar meses en orden calendario
orden_meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
               "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

df_est["Mes"] = pd.Categorical(df_est["Mes"], categories=orden_meses, ordered=True)
df_est = df_est.sort_values("Mes")

# Gráfica mejorada
fig = px.bar(
    df_est,
    x="Mes",
    y="Porcentaje (%)",
    title="Estacionalidad Mensual del Delito Dominante",
    text="Porcentaje (%)",  # valores encima de cada barra
    color="Porcentaje (%)",
    color_continuous_scale="Blues"
)

# Ajustes visuales profesionales
fig.update_traces(
    texttemplate='%{text:.1f}%',    # formato con 1 decimal + %
    textposition='outside'
)

fig.update_layout(
    title_font=dict(size=22, family="Arial", color="#333"),
    xaxis_title="Mes",
    yaxis_title="Porcentaje (%)",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(200,200,200,0.3)"),
    coloraxis_showscale=False,  # oculta la barra de color si no la quieres
    bargap=0.15,
    height=450
)

# Mostrar gráfica
st.plotly_chart(fig, use_container_width=True)

# ============================
# Ranking de Municipios
# Usamos municipios_resumen.json (ruta: models/descriptivo/classification_dominant/municipios_resumen.json) para mostrar ranking de municipios
# ============================

# Construcción de ruta compatible con varios sistemas operativos
json_path = os.path.join(
    BASE_DIR,
    "..",
    "models",
    "descriptivo",
    "classification_dominant",
    "municipios_resumen.json"
)

# Cargar JSON
with open(json_path, "r", encoding="utf-8") as f:
    mun = json.load(f)

# Construir DataFrame a partir del JSON real
df_mun = pd.DataFrame([
    {
        "codigo": k,
        "ranking": v["ranking_departamental"],
        "riesgo": v["categoria_riesgo"],
        "delito": v["delito_mas_frecuente"],
        "delitos": v["total_delitos"]
    }
    for k, v in mun.items()
]).sort_values("ranking")

# Selector para definir el tamaño del top
top_n = st.slider("Selecciona el TOP a visualizar", 5, 30, 10)

df_top = df_mun.head(top_n)

st.subheader(f"🏅 TOP {top_n} Municipios con mayor criminalidad")

COLOR_RIESGO = {
    "Alto": "#e74c3c",
    "Medio-Alto": "#f39c12",
    "Medio-Bajo": "#f1c40f",
    "Bajo": "#2ecc71",
}

for _, row in df_top.iterrows():

    card = st.container(border=True)
    col1, col2 = card.columns([1, 3])

    col1.write(f"### **#{row['ranking']}**")
    col1.write(
        f"<span style='color:{COLOR_RIESGO[row['riesgo']]}; font-weight:bold;'>"
        f"{row['riesgo']}"
        f"</span>",
        unsafe_allow_html=True
    )

    col2.write(f"**Municipio:** {row['codigo']}")
    col2.write(f"**Total delitos:** {row['delitos']:,}")
    col2.write(f"**Delito dominante:** {row['delito']}")


# ============================
# Mapa de Riesgo
# Usamos [categoria riesgo] de municipios_resumen.json y municipios.geojson (ruta: data/silver/dane_geo/geografia_silver.geojson) para mapa de riesgo por municipio
# ============================
import os
import json
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from branca.element import MacroElement, Template


# =====================
#    CARGA DE DATOS
# =====================

# JSON de riesgo por municipio
json_path = os.path.join(
    BASE_DIR,
    "..",
    "models", 
    "descriptivo", 
    "classification_dominant", 
    "municipios_resumen.json"
)

with open(json_path, "r", encoding="utf-8") as f:
    mun = json.load(f)

df_mun = pd.DataFrame([
    {
        "codigo": k,
        "ranking": v["ranking_departamental"],
        "riesgo": v["categoria_riesgo"],
        "delito_dom": v["delito_mas_frecuente"],
        "delitos": v["total_delitos"]
    }
    for k, v in mun.items()
])

# GeoJSON de municipios
geojson_path = os.path.join(
    BASE_DIR, 
    "..",
    "data", 
    "silver", 
    "dane_geo", 
    "geografia_silver.geojson"
)

with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)


# =====================
#       COLORES
# =====================

COLOR_RIESGO = {
    "Alto": "#e74c3c",
    "Medio-Alto": "#e67e22",
    "Medio-Bajo": "#f1c40f",
    "Bajo": "#2ecc71"
}

def get_color(riesgo):
    return COLOR_RIESGO.get(riesgo, "#bdc3c7")  # gris si no encuentra


# =====================
#   MAPA INTERACTIVO
# =====================

st.subheader("🗺️ Mapa de Riesgo por Municipio - Santander")

# Centro aproximado de Santander
m = folium.Map(
    location=[7.12539, -73.1198],
    zoom_start=8,
    tiles="CartoDB positron"
)

# Unión lógica con código
for feature in geojson_data["features"]:
    codigo = str(feature["properties"].get("codigo_municipio"))
    nombre_mun = feature["properties"].get("municipio", "-")

    row = df_mun[df_mun["codigo"] == codigo]
    if row.empty:
        color = "#bdc3c7"
        riesgo = "Sin datos"
        delito = "-"
        delitos = "-"
    else:
        row = row.iloc[0]
        color = get_color(row["riesgo"])
        riesgo = row["riesgo"]
        delito = row["delito_dom"]
        delitos = row["delitos"]

    # popup profesional con nombre del GeoJSON
    popup_html = f"""
    <div style="font-size: 14px;">
        <b>Municipio:</b> {nombre_mun}<br>
        <b>Riesgo:</b> {riesgo}<br>
        <b>Total delitos:</b> {delitos}<br>
        <b>Delito dominante:</b> {delito}
    </div>
    """

    folium.GeoJson(
        feature,
        style_function=lambda x, col=color: {
            "fillColor": col,
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.7
        },
        tooltip=popup_html
    ).add_to(m)

# =====================
# LEYENDA DE COLORES
# =====================
template = """
{% macro html(this, kwargs) %}
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 140px; height: 140px; 
            z-index:9999; font-size:14px;">
    <b>Riesgo:</b><br>
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

# Mostrar en Streamlit
st_folium(m, width=900, height=550)
 







st.markdown("""
<div class="card">
    <h3>🔍 Exploración de indicadores de seguridad</h3>
    <p>
    En esta sección podrás visualizar mapas interactivos, seleccionar municipios,
    comparar delitos y analizar tendencias históricas.
    </p>
</div>
""", unsafe_allow_html=True)
# ============================
# Filtros
# ============================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("🎛️ Filtros de exploración")

col1, col2, col3 = st.columns(3)

with col1:
    municipio = st.selectbox("Selecciona un municipio:", ["Bucaramanga", "Floridablanca", "Girón", "Piedecuesta"])

with col2:
    delito = st.selectbox("Tipo de delito:", ["Homicidio", "Hurto", "Delito sexual", "Violencia Intrafamiliar"])

with col3:
    año = st.selectbox("Año:", list(range(2015, 2025)))

st.markdown("</div>", unsafe_allow_html=True)




# ============================
# Placeholder de mapa
# ============================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("🗺️ Mapa geoespacial")

st.info("Aquí se cargará el mapa interactivo con niveles de riesgo, heatmaps y capas territoriales.")
st.markdown("</div>", unsafe_allow_html=True)
