import streamlit as st

def render():
    """Render the about/information page."""
    
    st.title("Información del Proyecto CrimeLab")

    st.markdown("""
    <div class="card">
        <h3>Documentación general</h3>
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
    st.subheader("Arquitectura del ecosistema")

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
    st.subheader("Metodología y fuentes")

    st.write("""
    Se utilizan fuentes oficiales como:
    - Policía Nacional  
    - Medicina Legal  
    - DANE  
    - Datos Abiertos  
    """)

    st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================
    # Modelos
    # ============================
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Modelos Analíticos")

    st.write("""
    CrimeLab incorpora múltiples modelos de Machine Learning:
    
    ### Modelos Descriptivos
    - **Clasificación Dominante:** Identifica el delito y arma más frecuentes por municipio.
    - **Clasificación de Eventos:** Analiza perfiles demográficos y contextuales.
    
    ### Modelos Predictivos
    - **Proyección Temporal:** Predicción de tendencias futuras basada en series de tiempo.
    - **Clasificación de Riesgo:** Categorización municipal según indicadores de criminalidad.
    """)

    st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================
    # Equipo
    # ============================
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Equipo de Desarrollo")

    st.write("""
    Este proyecto fue desarrollado como parte de una iniciativa de analítica 
    de datos para la seguridad ciudadana en el departamento de Santander.
    """)

    st.markdown("</div>", unsafe_allow_html=True)
