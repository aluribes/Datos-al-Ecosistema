import streamlit as st
import os

def render():
    """Render the home page content."""
    
    # Logo at top, centered
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(BASE_DIR, "assets", "logo_crimelab.png")
    
    if os.path.exists(logo_path):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, use_container_width=True)
    
    st.title("CrimeLab: Seguridad Ciudadana – Santander")

    st.markdown("""
    **CrimeLab** es la plataforma analítica diseñada para fortalecer la toma de decisiones 
    en materia de seguridad ciudadana en los 87 municipios del departamento de Santander.

    Integra datos oficiales, analítica geoespacial, modelos predictivos y un asistente inteligente 
    para facilitar el acceso a información confiable y actualizada.
    """)

    st.markdown("---")

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

    st.markdown("---")

    # ------------------------------
    # TARJETA 2 – Secciones del Tablero
    # ------------------------------
    st.markdown("## 📌 Secciones del Tablero")

    st.markdown("""
    ### **Visor Analítico**  
    Mapas interactivos, series temporales y filtros por municipio, tipo de delito y tendencia histórica.

    ### **Chatbot ALBA**  
    ALBA (**Asistente Local de Búsqueda y Análisis**) responde preguntas sobre seguridad ciudadana,  
    estadísticas, territorio, delitos y comparativos entre municipios.

    ### **Información del Proyecto**  
    Arquitectura del sistema, metodología, modelos, fuentes y documentación técnica.
    """)

    st.markdown("---")

    # ------------------------------
    # TARJETA 3 – Invitación
    # ------------------------------
    st.markdown("## 🚀 Explora CrimeLab")

    st.markdown("""
    Usa el menú de navegación para explorar las herramientas disponibles.  
    Cada módulo ha sido diseñado para brindar claridad, precisión y utilidad
    a quienes toman decisiones en temas de seguridad territorial.
    """)
