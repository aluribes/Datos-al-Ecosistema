import streamlit as st

st.set_page_config(
    page_title="Datos – CrimeLab",
    page_icon="📁",
    layout="wide"
)

st.title("📁 Datos del Ecosistema CrimeLab")

# ============================
# Tarjeta principal
# ============================
st.markdown("""
<div class="card">
    <h3>📦 Catálogo de datos disponibles</h3>
    <p>
    Aquí encontrarás información sobre los datasets procesados en los niveles
    <b>Bronze</b>, <b>Silver</b> y <b>Gold</b>, así como descargas y descripciones.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================
# Secciones
# ============================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("📊 Niveles del ecosistema de datos")

st.write("""
### 🥉 Bronze  
Datos crudos provenientes de fuentes oficiales.

### 🥈 Silver  
Datos limpiados, unificados y con tipologías estandarizadas.

### 🥇 Gold  
Datos enriquecidos y listos para modelos predictivos.
""")

st.markdown("</div>", unsafe_allow_html=True)

# ============================
# Descargas
# ============================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("⬇️ Descarga de datasets")

st.info("Aquí aparecerán botones para descargar los archivos procesados.")
st.markdown("</div>", unsafe_allow_html=True)
