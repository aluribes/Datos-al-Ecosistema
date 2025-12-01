import streamlit as st
from PIL import Image
import os

# ============================
# CONFIGURACIÓN GENERAL
# ============================
st.set_page_config(
    page_title="CrimeLab: Seguridad Ciudadana – Santander",
    page_icon="🛡️",
    layout="wide",
)

# ============================
# CARGAR ESTILOS EXTERNOS
# ============================
styles_path = os.path.join("assets", "styles.css")

if os.path.exists(styles_path):
    with open(styles_path, "r", encoding="utf-8", errors="ignore") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("⚠️ No se encontró assets/styles.css")

# ============================
# LOGO EN EL SIDEBAR
# ============================
logo_path = os.path.join("assets", "logo_crimelab.png")

if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.sidebar.markdown("<div class='logo-container'>", unsafe_allow_html=True)
    st.sidebar.image(logo, use_container_width=False, width=150)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
else:
    st.sidebar.write("⚠️ Agrega tu logo en assets/logo.png")

# ============================
# MENÚ LATERAL 
# ============================
def sidebar_link(icon, label, page):
    st.sidebar.markdown(
        f"""
        <a href="/{page}" target="_self" style="text-decoration:none;">
            <img src="assets/{icon}" class="menu-icon" style="width:22px;vertical-align:middle;margin-right:10px;">
            <span style="color:white;">{label}</span>
        </a><br><br>
        """,
        unsafe_allow_html=True
    )

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

sidebar_link("🏠", "Inicio", "")
sidebar_link(" 📊 ", "Visor Analítico", "1_Visor_Analitico")
sidebar_link(" 🤖 ", "ALBA", "2_Chatbot")
sidebar_link("📁", "Datos", "3_Datos")
sidebar_link("ℹ️", "Información", "4_Información")

# ============================
# CONTENIDO PRINCIPAL: INICIO
# ============================

st.title("CrimeLab: Seguridad Ciudadana – Santander")

st.markdown("""
**CrimeLab** es la plataforma analítica diseñada para fortalecer la toma de decisiones 
en materia de seguridad ciudadana en los 87 municipios del departamento de Santander.

Integra datos oficiales, analítica geoespacial, modelos predictivos y un asistente inteligente 
para facilitar el acceso a información confiable y actualizada.
""")

# ------------------------------
# TARJETA 1 – ¿Qué es CrimeLab?
# ------------------------------
st.markdown("## 🔍 ¿Qué es CrimeLab?")
st.markdown("""
CrimeLab es un ecosistema de datos y herramientas diseñado para:

- Analizar dinámicas de criminalidad y convivencia.
- Brindar visualizaciones claras e interactivas.
- Unificar fuentes de datos en un solo entorno.
- Apoyar la gestión pública con analítica avanzada.
""")

# ------------------------------
# TARJETA 2 – Secciones del Tablero
# ------------------------------
st.markdown("## 📌 Secciones del Tablero")

st.markdown("""
### 📊 **Visor Analítico**  
Mapas interactivos, series temporales y filtros por municipio, tipo de delito y tendencia histórica.

### 🤖 **Chatbot ALBA**  
ALBA (**Asistente Local de Búsqueda y Análisis**) responde preguntas sobre seguridad ciudadana,  
estadísticas, territorio, delitos y comparativos entre municipios.

### 📁 **Datos del Ecosistema**  
Accede a las bases procesadas, oro/silver/bronze, catálogo de datos y descargas.

### 📘 **Información del Proyecto**  
Arquitectura del sistema, metodología, modelos, fuentes y documentación técnica.
""")

# ------------------------------
# TARJETA 3 – Invitación
# ------------------------------
st.markdown("## 🚀 Explora CrimeLab")

st.markdown("""
Usa el menú lateral para navegar por las herramientas disponibles.  
Cada módulo ha sido diseñado para brindar claridad, precisión y utilidad
a quienes toman decisiones en temas de seguridad territorial.
""")
