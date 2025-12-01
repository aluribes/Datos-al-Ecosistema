import streamlit as st

def render():
    """Render the home page content."""
    
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

    ### 📘 **Información del Proyecto**  
    Arquitectura del sistema, metodología, modelos, fuentes y documentación técnica.
    """)

    # ------------------------------
    # TARJETA 3 – Invitación
    # ------------------------------
    st.markdown("## 🚀 Explora CrimeLab")

    st.markdown("""
    Usa el menú de navegación para explorar las herramientas disponibles.  
    Cada módulo ha sido diseñado para brindar claridad, precisión y utilidad
    a quienes toman decisiones en temas de seguridad territorial.
    """)
