import streamlit as st

def render():
    """Render the about/information page."""
    
    st.title("Información del Proyecto CrimeLab")

    # ============================
    # Metodología y Fuentes (moved to top)
    # ============================
    st.subheader("Metodología y fuentes")

    st.write("""
    Se utilizan fuentes oficiales como:
    - **Policía Nacional** – Estadísticas delictivas y reportes de seguridad
    - **Medicina Legal** – Datos forenses y de violencia
    - **DANE** – Información geográfica, demográfica y división política
    - **Datos Abiertos** – Datasets gubernamentales de acceso público
    """)

    st.markdown("---")

    # ============================
    # Arquitectura
    # ============================
    st.subheader("Arquitectura del ecosistema")

    st.write("""
    CrimeLab sigue un proceso estructurado para transformar datos crudos en información accionable:
    
    **1. Consulta e Ingesta de Datos**  
    Se recopilan datos de múltiples fuentes oficiales mediante APIs, web scraping y descargas directas.
    
    **2. Procesamiento con Arquitectura Medallion**  
    Los datos pasan por tres capas de transformación:
    - **Bronze:** Datos crudos tal como llegan de las fuentes.
    - **Silver:** Datos limpios, validados y estandarizados.
    - **Gold:** Datos agregados, enriquecidos y listos para análisis.
    
    **3. Modelado Analítico**  
    Se desarrollan modelos descriptivos y predictivos utilizando técnicas de Machine Learning 
    para identificar patrones, clasificar riesgos y proyectar tendencias.
    
    **4. Visualización e Interacción**  
    La información se presenta a través de esta aplicación Streamlit, que incluye dashboards 
    interactivos, mapas geoespaciales y un asistente conversacional.
    """)

    st.markdown("---")

    # ============================
    # Modelos
    # ============================
    st.subheader("Modelos Analíticos")

    st.write("""
    CrimeLab incorpora múltiples modelos de Machine Learning:
    
    **Modelos Descriptivos**
    - **Clasificación Dominante:** Identifica el delito y arma más frecuentes por municipio.
    - **Clasificación de Eventos:** Analiza perfiles demográficos y contextuales.
    
    **Modelos Predictivos**
    - **Proyección Temporal:** Predicción de tendencias futuras basada en series de tiempo.
    - **Clasificación de Riesgo:** Categorización municipal según indicadores de criminalidad.
    """)

    st.markdown("---")

    # ============================
    # Equipo
    # ============================
    st.subheader("Equipo de Desarrollo")

    st.write("""
    Este proyecto fue desarrollado por un equipo de 4 integrantes comprometidos 
    con el uso de datos para el impacto social en el departamento de Santander.
    """)

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Alejandra Uribe Sierra**  
        [LinkedIn](https://www.linkedin.com/in/alejandra-uribe-sierra)
        
        **Shorly López Pérez**  
        [LinkedIn](https://www.linkedin.com/in/shorly-lopez-perez)
        """)
    
    with col2:
        st.markdown("""
        **Sergio Luis López Verbel**  
        [LinkedIn](https://www.linkedin.com/in/sergio-luis-lopez-verbel)
        
        **Mateo Arenas Montoya**
        """)
