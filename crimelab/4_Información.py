import streamlit as st

st.set_page_config(
    page_title="Información del Proyecto – CrimeLab",
    page_icon="ℹ️",
    layout="wide"
)

st.title("ℹ️ Información del Proyecto CrimeLab")

st.markdown("""
<div class="card">
    <h3>📘 Documentación general</h3>
    <p>
    Esta sección contiene la descripción del proyecto, arquitectura,
    metodología, fuentes de datos y lineamientos técnicos.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================
# Arquitectura
# ============================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("🏗️ Arquitectura del ecosistema")

st.write("""
El sistema implementa una arquitectura tipo **Medallion** compuesta por:
- **Bronze:** ingestión de datos crudos.  
- **Silver:** transformación y estandarización.  
- **Gold:** datos optimizados para analítica, dashboards y modelos.  
""")

st.markdown("</div>", unsafe_allow_html=True)

# ============================
# Metodología
# ============================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("📐 Metodología y fuentes")

st.write("""
Se utilizan fuentes oficiales como:
- Policía Nacional  
- Medicina Legal  
- DANE  
- Datos Abiertos  
""")

st.markdown("</div>", unsafe_allow_html=True)
