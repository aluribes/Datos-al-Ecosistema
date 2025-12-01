import streamlit as st
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the base directory (crimelab folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_file_path(base_dir, *relative_path_components):
    """Generates a normalized path for any operating system."""
    return os.path.normpath(os.path.join(base_dir, *relative_path_components))


# ============================
# DATA LOADING FOR CONTEXT
# ============================

@st.cache_data(show_spinner="Cargando contexto para ALBA...")
def load_chatbot_context():
    """Load relevant data to provide context to the chatbot."""
    context_data = {}
    
    try:
        # Load descriptive statistics
        stats_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "classification_dominant", "estadisticas_generales.json")
        with open(stats_path, "r", encoding="utf-8") as f:
            context_data["stats"] = json.load(f)
        
        # Load municipality summary
        mun_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "classification_dominant", "municipios_resumen.json")
        with open(mun_path, "r", encoding="utf-8") as f:
            context_data["municipios"] = json.load(f)
        
        # Load trends
        tendencias_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "classification_dominant", "tendencias_anuales.json")
        with open(tendencias_path, "r", encoding="utf-8") as f:
            context_data["tendencias"] = json.load(f)
            
        # Load event summary
        event_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "classification_event", "resumen_general.json")
        with open(event_path, "r", encoding="utf-8") as f:
            context_data["eventos"] = json.load(f)
            
        # Load chatbot responses (pre-generated answers)
        chatbot_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "classification_event", "respuestas_chatbot.json")
        with open(chatbot_path, "r", encoding="utf-8") as f:
            context_data["respuestas_predefinidas"] = json.load(f)
            
        # Load GeoJSON for municipality names
        geojson_path = get_file_path(BASE_DIR, "..", "data", "silver", "dane_geo", "geografia_silver.geojson")
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson = json.load(f)
            municipio_map = {}
            for feature in geojson.get("features", []):
                codigo = str(feature["properties"].get("codigo_municipio"))
                nombre = feature["properties"].get("municipio")
                if codigo and nombre:
                    municipio_map[codigo] = nombre.upper()
            context_data["municipio_names"] = municipio_map
            
        return context_data
        
    except Exception as e:
        st.error(f"Error cargando contexto: {e}")
        return {}


def build_system_prompt(context_data):
    """Build the system prompt with relevant context data."""
    
    stats = context_data.get("stats", {})
    tendencias = context_data.get("tendencias", {})
    eventos = context_data.get("eventos", {})
    municipios = context_data.get("municipios", {})
    municipio_names = context_data.get("municipio_names", {})
    
    # Get top 10 municipalities by risk
    top_municipios = []
    for codigo, data in municipios.items():
        nombre = municipio_names.get(codigo, codigo)
        top_municipios.append({
            "nombre": nombre,
            "ranking": data.get("ranking_departamental", 999),
            "riesgo": data.get("categoria_riesgo", "N/A"),
            "delito_frecuente": data.get("delito_mas_frecuente", "N/A"),
            "total_delitos": data.get("total_delitos", 0)
        })
    top_municipios = sorted(top_municipios, key=lambda x: x["ranking"])[:10]
    
    system_prompt = f"""Eres ALBA (Asistente Local de Búsqueda y Análisis), un asistente virtual experto en seguridad ciudadana del departamento de Santander, Colombia.

Tu rol es ayudar a usuarios (funcionarios públicos, investigadores, ciudadanos) a entender las dinámicas de criminalidad en la región, basándote en datos oficiales procesados por el sistema CrimeLab.

## DATOS QUE CONOCES:

### Estadísticas Generales de Santander:
- Período de análisis: {stats.get('periodo', {}).get('inicio', 'N/A')} - {stats.get('periodo', {}).get('fin', 'N/A')}
- Total de delitos dominantes registrados: {stats.get('suma_delitos_dominantes', 'N/A'):,}
- Delito más frecuente: {stats.get('delito_mas_frecuente', {}).get('nombre', 'N/A')} ({stats.get('delito_mas_frecuente', {}).get('porcentaje', 0):.1f}% del total)
- Arma más utilizada: {stats.get('arma_mas_frecuente', {}).get('nombre', 'N/A')} ({stats.get('arma_mas_frecuente', {}).get('porcentaje', 0):.1f}% del total)
- Tendencia general: {tendencias.get('tendencia_general', 'N/A')}

### Eventos Registrados:
- Total de eventos analizados: {eventos.get('total_eventos', 'N/A'):,}
- Número de municipios: {eventos.get('geografia', {}).get('n_municipios', 'N/A')}
- Período: {eventos.get('periodo', {}).get('anio_inicio', 'N/A')} - {eventos.get('periodo', {}).get('anio_fin', 'N/A')}

### Top 10 Municipios por Riesgo:
{chr(10).join([f"- #{m['ranking']} {m['nombre']}: Riesgo {m['riesgo']}, {m['total_delitos']:,} delitos, delito más común: {m['delito_frecuente']}" for m in top_municipios])}

### Categorías de Riesgo:
- Alto: Municipios con mayor incidencia delictiva
- Medio-Alto: Incidencia significativa
- Medio-Bajo: Incidencia moderada
- Bajo: Menor incidencia delictiva

## INSTRUCCIONES:
1. Responde SIEMPRE en español.
2. Sé preciso y cita los datos cuando los tengas disponibles.
3. Si no tienes información específica sobre algo, indícalo claramente.
4. Puedes dar recomendaciones generales de seguridad pública basadas en los datos.
5. Mantén un tono profesional pero accesible.
6. Si te preguntan sobre un municipio específico y tienes datos, proporciónalos.
7. Si te preguntan sobre predicciones, explica que el sistema tiene modelos predictivos pero tú solo proporcionas información descriptiva histórica.
8. Mantén tus respuestas concisas pero informativas.

## MUNICIPIOS DE SANTANDER QUE CONOCES:
{', '.join(sorted(set(municipio_names.values())))}
"""
    
    return system_prompt


def get_municipality_context(municipio_query, context_data):
    """Get specific context about a municipality if mentioned in the query."""
    municipios = context_data.get("municipios", {})
    municipio_names = context_data.get("municipio_names", {})
    
    municipio_query_upper = municipio_query.upper()
    
    for codigo, nombre in municipio_names.items():
        if nombre in municipio_query_upper or municipio_query_upper in nombre:
            mun_data = municipios.get(codigo, {})
            if mun_data:
                return f"""
Información específica de {nombre}:
- Código DANE: {codigo}
- Ranking departamental: #{mun_data.get('ranking_departamental', 'N/A')}
- Categoría de riesgo: {mun_data.get('categoria_riesgo', 'N/A')}
- Delito más frecuente: {mun_data.get('delito_mas_frecuente', 'N/A')}
- Total de delitos: {mun_data.get('total_delitos', 0):,}
- Tendencia: {mun_data.get('tendencia', {}).get('direccion', 'N/A')} ({mun_data.get('tendencia', {}).get('cambio_vs_anio_anterior', 0):+.1f}% vs año anterior)
"""
    return ""


@st.cache_resource
def get_gemini_model():
    """Initialize and cache the Gemini model."""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None, "No se encontró la API key de Google. Verifica el archivo .env"
        
        genai.configure(api_key=api_key)
        
        # Use gemini-2.0-flash-lite as requested
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        return model, None
        
    except ImportError:
        return None, "El paquete google-generativeai no está instalado. Ejecuta: pip install google-generativeai"
    except Exception as e:
        return None, f"Error inicializando Gemini: {e}"


def chat_with_alba(user_message, context_data, chat_history):
    """Send a message to ALBA and get a response."""
    
    model, error = get_gemini_model()
    
    if error:
        return f"❌ {error}"
    
    if model is None:
        return "❌ No se pudo inicializar el modelo de IA."
    
    try:
        # Build system prompt with context
        system_prompt = build_system_prompt(context_data)
        
        # Get municipality-specific context if applicable
        mun_context = get_municipality_context(user_message, context_data)
        
        # Build conversation history for context
        history_text = ""
        for msg in chat_history[-6:]:  # Last 6 messages for context
            role = "Usuario" if msg["role"] == "user" else "ALBA"
            history_text += f"{role}: {msg['content']}\n"
        
        # Build the full prompt
        full_prompt = f"""{system_prompt}

{mun_context}

## HISTORIAL DE CONVERSACIÓN:
{history_text}

## MENSAJE ACTUAL DEL USUARIO:
{user_message}

## TU RESPUESTA:"""

        # Generate response
        response = model.generate_content(full_prompt)
        
        return response.text
        
    except Exception as e:
        return f"❌ Error generando respuesta: {e}"


def render():
    """Render the chatbot page."""
    
    st.title("ALBA - Asistente de Seguridad Ciudadana")
    
    st.markdown("""
    **ALBA** (Asistente Local de Búsqueda y Análisis) es un chatbot inteligente 
    diseñado para responder preguntas sobre seguridad ciudadana en Santander.
    
    Puedes preguntarle sobre:
    - Estadísticas de criminalidad
    - Información por municipio
    - Tendencias y patrones
    - Tipos de delitos más comunes
    - Clasificación de riesgo municipal
    """)
    
    st.markdown("---")
    
    # Load context data
    context_data = load_chatbot_context()
    
    if not context_data:
        st.error("No se pudo cargar el contexto de datos. Algunas funcionalidades pueden estar limitadas.")
    
    # Check if Gemini is available
    model, error = get_gemini_model()
    if error:
        st.warning(f"⚠️ {error}")
        st.info("El chatbot requiere la librería `google-generativeai`. Instálala con: `pip install google-generativeai`")
        return
    
    # Initialize chat history in session state
    if "alba_messages" not in st.session_state:
        st.session_state.alba_messages = [
            {
                "role": "assistant",
                "content": "¡Hola! Soy ALBA, tu asistente de seguridad ciudadana para Santander. ¿En qué puedo ayudarte hoy? Puedes preguntarme sobre estadísticas de criminalidad, información de municipios, tendencias, o cualquier duda sobre seguridad en la región."
            }
        ]
    
    # Display chat messages
    for message in st.session_state.alba_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Escribe tu pregunta aquí..."):
        # Add user message to history
        st.session_state.alba_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("ALBA está pensando..."):
                response = chat_with_alba(prompt, context_data, st.session_state.alba_messages)
            st.markdown(response)
        
        # Add assistant response to history
        st.session_state.alba_messages.append({"role": "assistant", "content": response})
    
    # Sidebar with quick actions
    with st.sidebar:
        st.markdown("### Preguntas sugeridas")
        
        suggestions = [
            "¿Cuál es el delito más común en Santander?",
            "¿Cuáles son los municipios más peligrosos?",
            "¿Cómo está la situación en Bucaramanga?",
            "¿Cuál es la tendencia de criminalidad?",
            "¿Qué armas se usan más frecuentemente?",
        ]
        
        for suggestion in suggestions:
            if st.button(suggestion, key=f"sug_{suggestion[:20]}"):
                st.session_state.alba_messages.append({"role": "user", "content": suggestion})
                response = chat_with_alba(suggestion, context_data, st.session_state.alba_messages)
                st.session_state.alba_messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        st.markdown("---")
        
        if st.button("Limpiar conversación"):
            st.session_state.alba_messages = [
                {
                    "role": "assistant",
                    "content": "¡Hola! Soy ALBA, tu asistente de seguridad ciudadana para Santander. ¿En qué puedo ayudarte hoy?"
                }
            ]
            st.rerun()
