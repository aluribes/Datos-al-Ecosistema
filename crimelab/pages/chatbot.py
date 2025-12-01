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
        # Load descriptive statistics (classification_dominant)
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
        
        # Load crime distribution
        dist_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "classification_event", "distribucion_delitos.json")
        with open(dist_path, "r", encoding="utf-8") as f:
            context_data["distribucion_delitos"] = json.load(f)
        
        # Load temporal analysis (crimes by year, month, etc.)
        temporal_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "classification_event", "analisis_temporal.json")
        with open(temporal_path, "r", encoding="utf-8") as f:
            context_data["analisis_temporal"] = json.load(f)
        
        # Load demographic analysis
        demo_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "classification_event", "analisis_demografico.json")
        with open(demo_path, "r", encoding="utf-8") as f:
            context_data["analisis_demografico"] = json.load(f)
        
        # Load geographic analysis (crimes per municipality with breakdown)
        geo_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "classification_event", "analisis_geografico.json")
        with open(geo_path, "r", encoding="utf-8") as f:
            context_data["analisis_geografico"] = json.load(f)
        
        # Load municipality statistics (monthly averages, last year totals, trends)
        mun_stats_path = get_file_path(BASE_DIR, "..", "models", "descriptivo", "regression_monthly", "estadisticas_por_municipio.json")
        with open(mun_stats_path, "r", encoding="utf-8") as f:
            context_data["estadisticas_municipio"] = json.load(f)
        
        # Load predictive model metadata
        pred_dominant_path = get_file_path(BASE_DIR, "..", "models", "predictivos", "classification_dominant", "metadata.json")
        with open(pred_dominant_path, "r", encoding="utf-8") as f:
            context_data["modelo_predictivo_dominant"] = json.load(f)
        
        pred_monthly_path = get_file_path(BASE_DIR, "..", "models", "predictivos", "regression_monthly", "metadata.json")
        with open(pred_monthly_path, "r", encoding="utf-8") as f:
            context_data["modelo_predictivo_monthly"] = json.load(f)
            
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
    distribucion = context_data.get("distribucion_delitos", {})
    temporal = context_data.get("analisis_temporal", {})
    demografico = context_data.get("analisis_demografico", {})
    respuestas = context_data.get("respuestas_predefinidas", {})
    modelo_pred = context_data.get("modelo_predictivo_dominant", {})
    modelo_regr = context_data.get("modelo_predictivo_monthly", {})
    geografico = context_data.get("analisis_geografico", {})
    estadisticas_mun = context_data.get("estadisticas_municipio", {})
    
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
    
    # Build crime distribution section
    dist_list = distribucion.get("distribucion", [])
    crime_stats = "\n".join([
        f"- {d['delito']}: {d['cantidad']:,} casos ({d['porcentaje']:.1f}%)" 
        for d in dist_list
    ])
    
    # Build yearly data section - ALL years with ALL crimes
    delitos_por_anio = temporal.get("delitos_por_anio", {})
    yearly_stats = []
    for anio in sorted(delitos_por_anio.keys(), reverse=True):
        data = delitos_por_anio[anio]
        total = sum(data.values())
        crimes_detail = ", ".join([f"{d}: {c:,}" for d, c in sorted(data.items(), key=lambda x: -x[1])])
        yearly_stats.append(f"- {anio} (Total: {total:,}): {crimes_detail}")
    yearly_section = "\n".join(yearly_stats)
    
    # Build per-crime detailed info from respuestas_por_delito
    crime_details = respuestas.get("respuestas_por_delito", {})
    crime_info = "\n".join([
        f"- {delito}: {info['total']:,} casos ({info['porcentaje']}%), perfil principal: {info['perfil_principal']}, grupo etario: {info['grupo_etario_mas_afectado']}"
        for delito, info in crime_details.items()
    ])
    
    # Build municipality crime info from respuestas_por_municipio
    mun_details = respuestas.get("respuestas_por_municipio", {})
    mun_info = "\n".join([
        f"- {mun}: {info['total']:,} delitos ({info['porcentaje']}%), delito más común: {info['delito_mas_comun']}"
        for mun, info in list(mun_details.items())[:15]
    ])
    
    # Build detailed municipality crime breakdown from analisis_geografico
    delitos_por_mun = geografico.get("delitos_por_municipio_top10", {})
    mun_crime_breakdown = []
    for mun, crimes in delitos_por_mun.items():
        crimes_list = ", ".join([f"{d}: {c:,}" for d, c in sorted(crimes.items(), key=lambda x: -x[1])])
        mun_crime_breakdown.append(f"- {mun}: {crimes_list}")
    mun_crime_section = "\n".join(mun_crime_breakdown)
    
    # Build municipality statistics summary (last year data, averages)
    mun_yearly_stats = []
    for codigo, mun_stat in sorted(estadisticas_mun.items(), key=lambda x: -x[1].get('ultimo_anio', {}).get('total', 0))[:15]:
        nombre = municipio_names.get(codigo, codigo)
        ultimo = mun_stat.get('ultimo_anio', {})
        mun_yearly_stats.append(
            f"- {nombre}: Último año: {ultimo.get('total', 0):,} delitos, "
            f"Promedio mensual: {mun_stat.get('promedio_mensual', 0):.1f}, "
            f"Variación anual: {mun_stat.get('variacion_anual_pct', 0):+.1f}%, "
            f"Tendencia: {mun_stat.get('tendencia', 'N/A')}"
        )
    mun_yearly_section = "\n".join(mun_yearly_stats)
    
    # Monthly analysis
    por_mes = temporal.get("por_mes", {}).get("distribucion", {})
    meses_nombres = {
        "1": "Enero", "2": "Febrero", "3": "Marzo", "4": "Abril",
        "5": "Mayo", "6": "Junio", "7": "Julio", "8": "Agosto",
        "9": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
    }
    monthly_stats = "\n".join([
        f"- {meses_nombres.get(m, m)}: {cant:,} delitos"
        for m, cant in sorted(por_mes.items(), key=lambda x: int(x[0]))
    ])
    
    # Demographic info
    genero = demografico.get("por_genero", {}).get("distribucion", {})
    genero_stats = ", ".join([f"{g}: {c:,}" for g, c in genero.items()])
    
    edad = demografico.get("por_grupo_etario", {}).get("distribucion", {})
    edad_stats = ", ".join([f"{e}: {c:,}" for e, c in edad.items()])
    
    system_prompt = f"""Eres ALBA (Asistente Local de Búsqueda y Análisis), un asistente virtual experto en seguridad ciudadana del departamento de Santander, Colombia.

Tu rol es ayudar a usuarios (funcionarios públicos, investigadores, ciudadanos) a entender las dinámicas de criminalidad en la región, basándote en datos oficiales procesados por el sistema CrimeLab.

## DATOS GENERALES DE SANTANDER:

### Período y Totales:
- Período de análisis: {stats.get('periodo', {}).get('inicio', 'N/A')} - {stats.get('periodo', {}).get('fin', 'N/A')}
- Total de eventos delictivos registrados: {eventos.get('total_eventos', 'N/A'):,}
- Número de municipios: {eventos.get('geografia', {}).get('n_municipios', 'N/A')}
- Tendencia general: {tendencias.get('tendencia_general', 'N/A')}

### DISTRIBUCIÓN COMPLETA DE DELITOS (Total: {distribucion.get('total', 0):,}):
{crime_stats}

### ESTADÍSTICAS DETALLADAS POR TIPO DE DELITO:
{crime_info}

### DELITOS POR AÑO (Últimos 5 años):
{yearly_section}

### DELITOS POR MES (Acumulado histórico):
{monthly_stats}

### ANÁLISIS DEMOGRÁFICO:
- Por género: {genero_stats}
- Por grupo etario: {edad_stats}
- Grupo más afectado: {demografico.get('por_grupo_etario', {}).get('grupo_mas_comun', 'N/A')}
- Perfil más común: {demografico.get('perfil_mas_comun', {}).get('nombre', 'N/A')} ({demografico.get('perfil_mas_comun', {}).get('porcentaje', 0):.1f}%)

### ESTADÍSTICAS TEMPORALES:
- Delitos en días laborales: {temporal.get('por_tipo_dia', {}).get('dia_laboral', 0):,}
- Delitos en fines de semana: {temporal.get('por_tipo_dia', {}).get('fin_de_semana', 0):,} ({temporal.get('por_tipo_dia', {}).get('pct_fin_semana', 0):.1f}%)
- Delitos en festivos: {temporal.get('festivos', {}).get('en_festivo', 0):,} ({temporal.get('festivos', {}).get('pct_festivo', 0):.1f}%)

### TOP 10 MUNICIPIOS POR RIESGO:
{chr(10).join([f"- #{m['ranking']} {m['nombre']}: Riesgo {m['riesgo']}, {m['total_delitos']:,} delitos, delito más común: {m['delito_frecuente']}" for m in top_municipios])}

### MUNICIPIOS CON MÁS DELITOS:
{mun_info}

### DESGLOSE DE DELITOS POR MUNICIPIO (Top 10, acumulado 2010-2025):
{mun_crime_section}

### ESTADÍSTICAS ANUALES POR MUNICIPIO (Top 15, datos del último año disponible):
{mun_yearly_section}

### MODELOS PREDICTIVOS DISPONIBLES:
1. Clasificación de delito y arma dominante (XGBoost MultiOutput)
   - Tipos de delito: {', '.join(modelo_pred.get('target_classes', {}).get('delito_dominante', []))}
   - Tipos de arma: {', '.join(modelo_pred.get('target_classes', {}).get('arma_dominante', []))}
   - Precisión delito: {modelo_pred.get('metrics', {}).get('delito_dominante', {}).get('accuracy', 0)*100:.1f}%

2. Regresión mensual de delitos (XGBoost)
   - R²: {modelo_regr.get('metrics', {}).get('R2', 0)*100:.1f}%
   - Error promedio: {modelo_regr.get('metrics', {}).get('MAE', 0):.1f} delitos

### CATEGORÍAS DE RIESGO:
- Alto: Municipios con mayor incidencia delictiva
- Medio-Alto: Incidencia significativa
- Medio-Bajo: Incidencia moderada
- Bajo: Menor incidencia delictiva

## INSTRUCCIONES:
1. Responde SIEMPRE en español.
2. USA LOS DATOS que tienes disponibles. Tienes estadísticas detalladas de TODOS los tipos de delito.
3. Si preguntan por un delito específico (homicidios, hurtos, etc.), busca la información en los datos que tienes.
4. Si preguntan por un año específico, consulta los datos por año que tienes.
5. Si preguntan por un municipio, proporciona toda la información disponible: último año, promedio mensual, variación anual, desglose de delitos.
6. Para preguntas sobre "el último año" o "este año", usa los datos de "último año" que tienes por municipio.
7. Sé preciso y cita números específicos cuando los tengas.
8. Si no tienes información específica sobre algo, indícalo claramente.
9. Mantén un tono profesional pero accesible.
10. Mantén tus respuestas concisas pero informativas.

## MUNICIPIOS DE SANTANDER:
{', '.join(sorted(set(municipio_names.values())))}
"""
    
    return system_prompt


def get_municipality_context(municipio_query, context_data):
    """Get specific context about a municipality if mentioned in the query."""
    municipios = context_data.get("municipios", {})
    municipio_names = context_data.get("municipio_names", {})
    respuestas = context_data.get("respuestas_predefinidas", {})
    mun_details = respuestas.get("respuestas_por_municipio", {})
    geografico = context_data.get("analisis_geografico", {})
    delitos_por_mun = geografico.get("delitos_por_municipio_top10", {})
    estadisticas_mun = context_data.get("estadisticas_municipio", {})
    
    municipio_query_upper = municipio_query.upper()
    
    for codigo, nombre in municipio_names.items():
        if nombre in municipio_query_upper or municipio_query_upper in nombre:
            mun_data = municipios.get(codigo, {})
            mun_resp = mun_details.get(nombre, {})
            mun_stats = estadisticas_mun.get(codigo, {})
            
            # Get crime breakdown for this municipality if available
            crime_breakdown = delitos_por_mun.get(nombre, {})
            crime_list = "\n".join([f"  • {d}: {c:,} casos" for d, c in sorted(crime_breakdown.items(), key=lambda x: -x[1])]) if crime_breakdown else "No disponible"
            
            # Get monthly/yearly statistics
            ultimo_anio = mun_stats.get("ultimo_anio", {})
            meses_nombres = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                           7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
            mes_critico = meses_nombres.get(mun_stats.get("mes_mas_delitos", 0), "N/A")
            
            if mun_data:
                return f"""
## INFORMACIÓN ESPECÍFICA DE {nombre}:
- Código DANE: {codigo}
- Ranking departamental: #{mun_data.get('ranking_departamental', 'N/A')}
- Categoría de riesgo: {mun_data.get('categoria_riesgo', 'N/A')}
- Total de delitos (histórico 2010-2025): {mun_stats.get('total_historico', mun_data.get('total_delitos', 0)):,}
- Porcentaje del total departamental: {mun_resp.get('porcentaje', 'N/A')}%
- Delito más frecuente: {mun_data.get('delito_mas_frecuente', 'N/A')}
- Tendencia: {mun_stats.get('tendencia', mun_data.get('tendencia', {}).get('direccion', 'N/A'))}

### ESTADÍSTICAS MENSUALES:
- Promedio mensual: {mun_stats.get('promedio_mensual', 0):.1f} delitos/mes
- Mediana mensual: {mun_stats.get('mediana_mensual', 0):.1f} delitos/mes
- Máximo mensual registrado: {mun_stats.get('maximo_mensual', 0):,} delitos
- Mes más crítico históricamente: {mes_critico}

### ÚLTIMO AÑO (datos más recientes):
- Total delitos último año: {ultimo_anio.get('total', 0):,}
- Promedio mensual último año: {ultimo_anio.get('promedio', 0):.1f} delitos/mes
- Variación vs año anterior: {mun_stats.get('variacion_anual_pct', 0):+.1f}%

### DATOS DEMOGRÁFICOS:
- Población: {mun_stats.get('poblacion', 0):,} habitantes
- Densidad poblacional: {mun_stats.get('densidad', 0):.1f} hab/km²

### DESGLOSE DE DELITOS EN {nombre} (Acumulado 2010-2025):
{crime_list}
"""
    return ""


@st.cache_resource(show_spinner=False)
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
    
    # Title with clear button on the right
    col_title, col_clear = st.columns([10, 1])
    with col_title:
        st.title("ALBA - Asistente de Seguridad Ciudadana")
    with col_clear:
        st.write("")  # Spacer to align with title
        if st.button("🗑️", help="Limpiar conversación", key="clear_chat"):
            st.session_state.alba_messages = [
                {
                    "role": "assistant",
                    "content": "¡Hola! Soy ALBA, tu asistente de seguridad ciudadana para Santander. ¿En qué puedo ayudarte hoy?"
                }
            ]
            st.rerun()
    
    st.markdown("""
    **ALBA** (Asistente Local de Búsqueda y Análisis) es un chatbot inteligente 
    diseñado para responder preguntas sobre seguridad ciudadana en Santander.
    """)
    
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
    
    # Suggested questions as inline buttons
    st.markdown("##### Preguntas sugeridas:")
    suggestions = [
        "¿Cuál es el delito más común en Santander?",
        "¿Cuáles son los municipios más peligrosos?",
        "¿Cómo está la situación en Bucaramanga?",
        "¿Cuál es la tendencia de criminalidad?",
        "¿Qué armas se usan más frecuentemente?",
    ]
    
    cols = st.columns(len(suggestions))
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state.alba_messages.append({"role": "user", "content": suggestion})
                response = chat_with_alba(suggestion, context_data, st.session_state.alba_messages)
                st.session_state.alba_messages.append({"role": "assistant", "content": response})
                st.rerun()
    
    st.markdown("---")
    
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
