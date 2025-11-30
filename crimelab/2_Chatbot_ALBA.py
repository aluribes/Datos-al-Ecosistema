import streamlit as st

st.set_page_config(
    page_title="Chatbot ALBA – CrimeLab",
    page_icon="🤖",
    layout="wide"
)

# ============================
# Título
# ============================
st.title("🤖 Chatbot ALBA – Asistente Local de Búsqueda y Análisis")

st.markdown("""
<div class="card">
    <h3>💬 Consulta datos y análisis de seguridad</h3>
    <p>
    ALBA es un asistente inteligente que puede responder preguntas sobre criminalidad,
    comparaciones entre municipios, tendencias y análisis de contexto territorial.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================
# Chatbot UI
# ============================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("🗨️ Chat en tiempo real")

user_query = st.text_input("Escribe tu pregunta:")

if user_query:
    st.success("Respuesta de ALBA:")
    st.write("_Aquí aparecerá la respuesta generada por tu modelo o API._")

st.markdown("</div>", unsafe_allow_html=True)
