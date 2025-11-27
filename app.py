# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

st.set_page_config(
    page_title="Seguridad Ciudadana Santander",
    layout="wide"
)

# ============================================================
# 1. Carga de datos (usa cache para acelerar)
# ============================================================

BASE_PATH = Path("data/gold")


@st.cache_data(show_spinner=True)
def load_base_data():
    """Carga todos los datasets base."""
    divipola = pd.read_parquet(BASE_PATH / "base" / "divipola_gold.parquet")
    geo = pd.read_parquet(BASE_PATH / "base" / "geo_gold.parquet")
    poblacion = pd.read_parquet(BASE_PATH / "base" / "poblacion_gold.parquet")
    policia = pd.read_parquet(BASE_PATH / "base" / "policia_gold.parquet")
    return {
        "divipola": divipola,
        "geo": geo,
        "poblacion": poblacion,
        "policia": policia,
    }


@st.cache_data(show_spinner=True)
def load_integrated_data():
    """Carga el dataset integrado principal (nivel de hechos)."""
    df = pd.read_parquet(BASE_PATH / "gold_integrado.parquet")
    return df


@st.cache_data(show_spinner=True)
def load_analytics_data():
    """Carga el dataset ya agregado para análisis (si lo usas)."""
    df = pd.read_parquet(BASE_PATH / "analytics" / "gold_analytics.parquet")
    return df


# ============================================================
# 2. Helpers para filtros y nombres de columnas
# ============================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea un alias de columnas en minúsculas para facilitar filtros
    sin alterar el DataFrame original.
    """
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df


def guess_column(df: pd.DataFrame, candidates):
    """
    Intenta adivinar una columna entre varias candidatas.
    candidates puede ser ['anio', 'year', 'ano'] por ejemplo.
    Retorna el nombre encontrado o None.
    """
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        cand_lower = cand.lower()
        if cand_lower in cols:
            return cols[cand_lower]
    return None


# ============================================================
# 3. TAB 1 - Dashboard
# ============================================================

def dashboard_tab(df_integrado: pd.DataFrame):
    st.subheader("📊 Dashboard de Seguridad Ciudadana")

    df = normalize_columns(df_integrado)

    # 👉 AJUSTAR estas listas de candidatos según tus columnas reales
    col_anio = guess_column(df, ["anio", "year", "ano"])
    col_depto = guess_column(df, ["departamento", "dpto", "depto"])
    col_mpio = guess_column(df, ["municipio", "mpio", "muni", "nombre_municipio"])
    col_delito = guess_column(df, ["tipo_delito", "delito", "categoria_delito"])
    col_casos = guess_column(df, ["casos", "n_hechos", "conteo", "num_casos"])
    col_tasa = guess_column(df, ["tasa_100k", "tasa", "tasa_x_100k"])

    if col_anio is None:
        st.error("No pude encontrar la columna de año. Revisa los nombres y ajusta el código.")
        st.stop()

    # ---- Filtros en la sidebar ----
    with st.sidebar:
        st.header("Filtros")
        anios = sorted(df[col_anio].dropna().unique().tolist())
        sel_anio = st.multiselect("Años", anios, default=anios[-1:])

        if col_depto:
            deptos = sorted(df[col_depto].dropna().unique().tolist())
            sel_depto = st.multiselect("Departamentos", deptos, default=deptos)
        else:
            sel_depto = []

        if col_mpio:
            # Filtrar municipios según deptos si aplica
            df_mpios = df.copy()
            if col_depto and sel_depto:
                df_mpios = df_mpios[df_mpios[col_depto].isin(sel_depto)]

            mpios = sorted(df_mpios[col_mpio].dropna().unique().tolist())
            sel_mpio = st.multiselect("Municipios", mpios, default=mpios[:10])
        else:
            sel_mpio = []

        if col_delito:
            delitos = sorted(df[col_delito].dropna().unique().tolist())
            sel_delito = st.multiselect("Tipo de delito", delitos, default=delitos)
        else:
            sel_delito = []

    # ---- Aplicar filtros ----
    mask = df[col_anio].isin(sel_anio)
    if col_depto and sel_depto:
        mask &= df[col_depto].isin(sel_depto)
    if col_mpio and sel_mpio:
        mask &= df[col_mpio].isin(sel_mpio)
    if col_delito and sel_delito:
        mask &= df[col_delito].isin(sel_delito)

    df_filt = df[mask]

    # ---- KPIs ----
    kpi_cols = st.columns(3)

    with kpi_cols[0]:
        if col_casos:
            total_casos = df_filt[col_casos].sum()
            st.metric("Total de casos (filtro actual)", f"{int(total_casos):,}".replace(",", "."))
        else:
            st.metric("Total de registros (filtro actual)", f"{len(df_filt):,}".replace(",", "."))

    with kpi_cols[1]:
        if col_tasa:
            tasa_prom = df_filt[col_tasa].mean()
            st.metric("Tasa promedio (por 100.000 hab.)", f"{tasa_prom:,.2f}")
        else:
            st.metric("Tasa promedio", "N/D")

    with kpi_cols[2]:
        st.metric("Años seleccionados", ", ".join(map(str, sel_anio)))

    st.markdown("---")

    # ---- Gráfico de tendencias por año ----
    st.markdown("### Tendencia temporal")

    if col_casos:
        df_time = (
            df_filt
            .groupby(col_anio, as_index=False)[col_casos]
            .sum()
            .sort_values(col_anio)
        )

        chart = (
            alt.Chart(df_time)
            .mark_line(point=True)
            .encode(
                x=alt.X(col_anio, title="Año"),
                y=alt.Y(col_casos, title="Número de casos"),
                tooltip=[col_anio, col_casos],
            )
            .properties(height=350)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No se encontró una columna de conteo de casos para graficar tendencia.")

    st.markdown("### Distribución por municipio")

    if col_mpio and col_casos:
        df_muni = (
            df_filt
            .groupby(col_mpio, as_index=False)[col_casos]
            .sum()
            .sort_values(col_casos, ascending=False)
            .head(20)
        )

        chart_muni = (
            alt.Chart(df_muni)
            .mark_bar()
            .encode(
                x=alt.X(col_casos, title="Número de casos"),
                y=alt.Y(col_mpio, sort="-x", title="Municipio"),
                tooltip=[col_mpio, col_casos],
            )
            .properties(height=500)
        )
        st.altair_chart(chart_muni, use_container_width=True)
    else:
        st.info("No se pudo construir la gráfica por municipio. Revisa las columnas de municipio/casos.")

    st.markdown("### Tabla de detalle (primeras filas)")
    st.dataframe(df_filt.head(200))


# ============================================================
# 4. TAB 2 - Chatbot (agente simple)
# ============================================================

def explain_stats(df: pd.DataFrame, pregunta: str):
    """
    Motor muy sencillo de "chatbot" basado en palabras clave.
    Toma la pregunta, intenta detectar delito, municipio y año más reciente,
    y devuelve un texto explicativo + rutas de atención.
    """
    df = normalize_columns(df)

    col_anio = guess_column(df, ["anio", "year", "ano"])
    col_mpio = guess_column(df, ["municipio", "mpio", "muni"])
    col_delito = guess_column(df, ["tipo_delito", "delito"])
    col_casos = guess_column(df, ["casos", "n_hechos", "conteo", "num_casos"])
    col_tasa = guess_column(df, ["tasa_100k", "tasa"])

    texto = pregunta.lower()

    # Detectar delito (muy simplificado)
    mapa_delitos = {
        "homicid": "HOMICIDIO",
        "hurto": "HURTO",
        "robo": "HURTO",
        "violencia intrafamiliar": "VIOLENCIA INTRAFAMILIAR",
        "intrafamiliar": "VIOLENCIA INTRAFAMILIAR",
        "sexual": "DELITOS SEXUALES",
        "informatic": "DELITOS INFORMÁTICOS",
    }
    delito_detectado = None
    for k, v in mapa_delitos.items():
        if k in texto:
            delito_detectado = v
            break

    # Detectar municipio si existe columna
    muni_detectado = None
    if col_mpio:
        for muni in df[col_mpio].dropna().unique():
            if str(muni).lower() in texto:
                muni_detectado = muni
                break

    # Año más reciente disponible
    anio_ref = None
    if col_anio:
        anio_ref = df[col_anio].max()

    # Construir filtro
    df_filt = df.copy()
    filtros = []
    if delito_detectado and col_delito:
        df_filt = df_filt[df_filt[col_delito] == delito_detectado]
        filtros.append(f"delito = **{delito_detectado}**")
    if muni_detectado and col_mpio:
        df_filt = df_filt[df_filt[col_mpio] == muni_detectado]
        filtros.append(f"municipio = **{muni_detectado}**")
    if anio_ref and col_anio:
        df_filt = df_filt[df_filt[col_anio] == anio_ref]
        filtros.append(f"año = **{anio_ref}**")

    resumen = ""
    if df_filt.empty:
        resumen = "Con la información disponible no encontré registros que coincidan con tu pregunta. " \
                  "Prueba siendo más general (por ejemplo, sólo por tipo de delito o año)."
    else:
        total = df_filt[col_casos].sum() if col_casos else len(df_filt)
        if col_tasa:
            tasa_prom = df_filt[col_tasa].mean()
            resumen = (
                f"Con los filtros {', '.join(filtros)}, se registran **{int(total):,} casos** "
                f"y una **tasa promedio de {tasa_prom:,.2f} por cada 100.000 habitantes**."
            )
        else:
            resumen = (
                f"Con los filtros {', '.join(filtros)}, se registran **{int(total):,} casos** "
                f"(no tengo columna de tasa disponible en este dataset)."
            )

    # Rutas de atención genéricas (puedes personalizar con tu policia_gold)
    rutas = """
**Rutas de atención recomendadas**

- Emergencias y situaciones en curso: **línea 123** (Policía Nacional).
- Violencia intrafamiliar y delitos sexuales:
  - **Comisarías de Familia** del municipio.
  - **Línea 155** (orientación a mujeres).
- Denuncias formales:
  - Fiscalía General de la Nación (URI / CAI / Casas de Justicia).
  - Estaciones de Policía más cercanas.

Recuerda que estos datos son estadísticos y no reemplazan las rutas oficiales de atención inmediata.
"""

    respuesta = resumen + "\n\n" + rutas
    return respuesta


def chatbot_tab(df_integrado: pd.DataFrame):
    st.subheader("🤖 Chat comunitario de datos y rutas de atención")

    st.markdown(
        """
Este chatbot **no usa ningún servicio pago**: 
se basa en reglas sencillas y en los datos cargados para darte un resumen estadístico 
y recordarte las rutas de atención.  
Puedes preguntar cosas como:

- *"¿Cómo están los homicidios en Bucaramanga?"*  
- *"¿Qué pasa con los hurtos en Santander en el último año?"*  
- *"¿Cómo van los delitos sexuales en el departamento?"*
"""
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.container():
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"**Tú:** {msg['content']}")
            else:
                st.markdown(f"**Asistente:** {msg['content']}")

    pregunta = st.text_input("Escribe tu pregunta:", value="", max_chars=300)

    if st.button("Enviar", type="primary") and pregunta.strip():
        st.session_state.chat_history.append({"role": "user", "content": pregunta})
        respuesta = explain_stats(df_integrado, pregunta)
        st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
        st.experimental_rerun()

    if st.button("🗑️ Limpiar conversación"):
        st.session_state.chat_history = []
        st.experimental_rerun()


# ============================================================
# 5. TAB 3 - Modelo predictivo (baseline)
# ============================================================

def simple_baseline_prediction(df: pd.DataFrame, municipio: str, delito: str, anio_objetivo: int):
    """
    Baseline muy simple: promedio de los últimos N años disponibles
    para ese municipio y delito. Se puede sustituir fácilmente por
    un modelo real (RandomForest, XGBoost, etc.).
    """
    df = normalize_columns(df)

    col_anio = guess_column(df, ["anio", "year", "ano"])
    col_mpio = guess_column(df, ["municipio", "mpio", "muni"])
    col_delito = guess_column(df, ["tipo_delito", "delito"])
    col_casos = guess_column(df, ["casos", "n_hechos", "conteo", "num_casos"])

    if not all([col_anio, col_mpio, col_delito, col_casos]):
        return None, "Faltan columnas necesarias para calcular la predicción (año, municipio, delito, casos)."

    df_filt = df[(df[col_mpio] == municipio) & (df[col_delito] == delito)]

    if df_filt.empty:
        return None, "No hay datos históricos para ese municipio y delito."

    # Tomar últimos N años antes del objetivo
    df_hist = df_filt[df_filt[col_anio] < anio_objetivo]
    if df_hist.empty:
        return None, "No hay años anteriores al objetivo para calcular promedio."

    df_agr = df_hist.groupby(col_anio)[col_casos].sum().reset_index()
    pred = df_agr[col_casos].tail(3).mean()  # promedio últimos 3 años

    detalle = df_agr.tail(5).rename(
        columns={col_anio: "Año", col_casos: "Casos"}
    )
    return pred, detalle


def prediction_tab(df_integrado: pd.DataFrame):
    st.subheader("🔮 Modelo predictivo (baseline histórico)")

    st.markdown(
        """
Este módulo usa un modelo **muy simple** a modo de ejemplo:  
calcula la predicción como el **promedio de los últimos 3 años** disponibles
para el municipio y delito seleccionados.

En tu versión final, aquí puedes reemplazar esa lógica por tu modelo real 
(entrenado con `gold_analytics.parquet` o los archivos de `model/`).
"""
    )

    df = normalize_columns(df_integrado)

    col_anio = guess_column(df, ["anio", "year", "ano"])
    col_mpio = guess_column(df, ["municipio", "mpio", "muni"])
    col_delito = guess_column(df, ["tipo_delito", "delito"])
    col_casos = guess_column(df, ["casos", "n_hechos", "conteo", "num_casos"])

    if not all([col_anio, col_mpio, col_delito, col_casos]):
        st.error(
            "Faltan columnas básicas para la predicción. "
            "Asegúrate de tener columnas de año, municipio, tipo de delito y casos, "
            "y ajusta los nombres en el código."
        )
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        municipios = sorted(df[col_mpio].dropna().unique().tolist())
        municipio_sel = st.selectbox("Municipio", municipios)

    with col2:
        delitos = sorted(df[col_delito].dropna().unique().tolist())
        delito_sel = st.selectbox("Tipo de delito", delitos)

    anio_min = int(df[col_anio].min())
    anio_max = int(df[col_anio].max())
    anio_obj = st.number_input(
        "Año a predecir",
        min_value=anio_max + 1,
        max_value=anio_max + 10,
        value=anio_max + 1,
        step=1
    )

    if st.button("Calcular predicción", type="primary"):
        pred, detalle = simple_baseline_prediction(df, municipio_sel, delito_sel, anio_obj)
        if pred is None:
            st.warning(detalle)
        else:
            st.success(
                f"Predicción para **{municipio_sel}**, delito **{delito_sel}** en el año **{anio_obj}**:"
            )
            st.metric("Casos estimados (baseline)", f"{pred:,.0f}")
            st.markdown("**Histórico reciente usado para la predicción:**")
            st.dataframe(detalle)


# ============================================================
# 6. MAIN
# ============================================================

def main():
    st.title("Tablero Inteligente de Seguridad Ciudadana - Santander")

    # Carga de datos
    try:
        base_data = load_base_data()
        df_integrado = load_integrated_data()
        # df_analytics = load_analytics_data()  # por si lo quieres usar luego
    except Exception as e:
        st.error(f"Error cargando los datos: {e}")
        st.stop()

    tab1, tab2, tab3 = st.tabs([
        "📊 Dashboard",
        "🤖 Chatbot comunitario",
        "🔮 Modelo predictivo",
    ])

    with tab1:
        dashboard_tab(df_integrado)

    with tab2:
        chatbot_tab(df_integrado)

    with tab3:
        prediction_tab(df_integrado)


if __name__ == "__main__":
    main()
