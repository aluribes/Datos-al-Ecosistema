# app.py
"""
Dashboard de Seguridad Ciudadana - Santander
============================================

Usa las tablas de data/gold/dashboard:

    - metas.parquet
    - mandatos.parquet
    - poblacion_santander.parquet
    - policia_santander.parquet
    - municipios.parquet
    - delitos_bucaramanga.parquet
    - delitos_informaticos.parquet

Simula el modelo relacional uniéndolas en memoria para:

    - Dashboard descriptivo
    - Chat de datos (agente sencillo)
    - Modelo predictivo baseline (promedio histórico)
"""

from pathlib import Path
from typing import Dict, List, Tuple

import os
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    print("DEBUG: API Key encontrada.")
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("DEBUG: API Key NO encontrada.")
    st.warning("⚠️ No se encontró la variable GOOGLE_API_KEY en el archivo .env. El chatbot no funcionará correctamente.")

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Seguridad Ciudadana - Santander",
    layout="wide",
)

DATA_DIR = Path("data/gold/dashboard")


# ============================================================
# 1. Carga de datos y construcción del modelo integrado
# ============================================================

@st.cache_data(show_spinner=True)
def load_base_tables() -> Dict[str, pd.DataFrame]:
    """Carga las tablas base del dashboard desde data/gold/dashboard."""
    metas = pd.read_parquet(DATA_DIR / "metas.parquet")
    mandatos = pd.read_parquet(DATA_DIR / "mandatos.parquet")
    poblacion = pd.read_parquet(DATA_DIR / "poblacion_santander.parquet")
    policia = pd.read_parquet(DATA_DIR / "policia_santander.parquet")
    municipios = pd.read_parquet(DATA_DIR / "municipios.parquet")
    delitos_bucaramanga = pd.read_parquet(DATA_DIR / "delitos_bucaramanga.parquet")
    delitos_informaticos = pd.read_parquet(DATA_DIR / "delitos_informaticos.parquet")

    # Normalizar nombres de columnas (quitar espacios)
    for df in (
        metas,
        mandatos,
        poblacion,
        policia,
        municipios,
        delitos_bucaramanga,
        delitos_informaticos,
    ):
        df.columns = [c.strip() for c in df.columns]

    return {
        "metas": metas,
        "mandatos": mandatos,
        "poblacion": poblacion,
        "policia": policia,
        "municipios": municipios,
        "delitos_bucaramanga": delitos_bucaramanga,
        "delitos_informaticos": delitos_informaticos,
    }


def build_integrated_df(
    metas: pd.DataFrame,
    mandatos: pd.DataFrame,
    poblacion: pd.DataFrame,
    policia: pd.DataFrame,
    municipios: pd.DataFrame,
    delitos_bucaramanga: pd.DataFrame,
    delitos_informaticos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construye un DataFrame integrado a nivel de hecho delictivo,
    uniendo las fuentes:

        - policia_santander          (SCRAPING)
        - delitos_bucaramanga        (Socrata local)
        - delitos_informaticos       (Socrata departamental)

    y luego simulando el modelo relacional:

        + municipios
        + poblacion_santander
        + mandatos
        + metas
    """
    # Copias de trabajo
    df_pol = policia.copy()
    df_buc = delitos_bucaramanga.copy()
    df_inf = delitos_informaticos.copy()

    # ---------------------------
    # Alinear columnas clave
    # ---------------------------

    # Bucaramanga: edad -> edad_persona
    if "edad" in df_buc.columns and "edad_persona" not in df_buc.columns:
        df_buc = df_buc.rename(columns={"edad": "edad_persona"})

    # Asegurar cantidad numérica
    for df_src in (df_pol, df_buc, df_inf):
        if "cantidad" in df_src.columns:
            df_src["cantidad"] = pd.to_numeric(df_src["cantidad"], errors="coerce").fillna(0)

    # Delitos informáticos no traen columna "delito" en el modelo,
    # creamos un identificador genérico para integrarlos.
    if "delito" not in df_inf.columns:
        df_inf["delito"] = "DELITOS INFORMÁTICOS"

    # Origen para trazabilidad
    df_pol["origen"] = "POLICIA_SCRAPING"
    df_buc["origen"] = "DELITOS_BUCARAMANGA"
    df_inf["origen"] = "DELITOS_INFORMATICOS"

    # Unificar hechos
    fact = pd.concat(
        [df_pol, df_buc, df_inf],
        ignore_index=True,
        sort=False,
    )

    # Limpieza básica de nombres antes de joins
    fact.columns = [c.strip() for c in fact.columns]

    # Eliminamos columnas espaciales que vendrán de municipios
    for col in ["departamento", "municipio", "codigo_departamento"]:
        if col in fact.columns:
            fact = fact.drop(columns=col)

    # ---------------------------
    # Join dimensión espacial (municipios)
    # ---------------------------
    fact = fact.merge(
        municipios[
            [
                "codigo_municipio",
                "codigo_departamento",
                "departamento",
                "municipio",
            ]
        ],
        on="codigo_municipio",
        how="left",
    )

    # ---------------------------
    # Join población (para tasas)
    # ---------------------------
    fact = fact.merge(
        poblacion[["codigo_municipio", "anio", "n_poblacion"]],
        on=["codigo_municipio", "anio"],
        how="left",
    )

    # ---------------------------
    # Join mandatos y metas
    # ---------------------------
    fact = fact.merge(mandatos, on="anio", how="left")  # agrega "mandato"
    fact = fact.merge(metas, on="mandato", how="left")  # agrega metas y presupuesto

    # ---------------------------
    # Tipos básicos y tasas
    # ---------------------------
    fact["anio"] = pd.to_numeric(fact["anio"], errors="coerce").astype("Int64")
    fact["mes"] = pd.to_numeric(fact["mes"], errors="coerce").astype("Int64")
    fact["dia"] = pd.to_numeric(fact["dia"], errors="coerce").astype("Int64")

    fact["delito"] = fact["delito"].astype(str).str.upper()
    fact["municipio"] = fact["municipio"].astype(str).str.upper()

    # Tasa por 100.000 habitantes (cuando hay población)
    fact["tasa_100k"] = np.where(
        fact["n_poblacion"] > 0,
        fact["cantidad"] / fact["n_poblacion"] * 1e5,
        np.nan,
    )

    return fact


# ============================================================
# 2. Helpers genéricos (normalización y agregaciones)
# ============================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas (strip) y retorna copia."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df


def crime_rate_and_meta(
    df: pd.DataFrame,
    crime_filter,
    meta_col: str,
) -> Tuple[float, float]:
    """
    Calcula:

        - tasa_real: casos totales / población total * 100.000
        - meta_tasa: meta departamental promedio (ya viene como tasa por 100.000)

    crime_filter puede ser un string o una lista de delitos.
    """
    if isinstance(crime_filter, str):
        mask = df["delito"] == crime_filter
    else:
        mask = df["delito"].isin(crime_filter)

    df_crime = df[mask].copy()
    if df_crime.empty:
        return 0.0, 0.0

    casos_tot = float(df_crime["cantidad"].sum())
    pob_tot = float(df_crime["n_poblacion"].fillna(0).sum())

    tasa_real = (casos_tot / pob_tot * 1e5) if pob_tot > 0 else 0.0

    meta_tasa = 0.0
    if meta_col in df_crime.columns:
        metas = (
            df_crime[["anio", meta_col]]
            .dropna()
            .drop_duplicates()
        )
        if not metas.empty:
            meta_tasa = float(metas[meta_col].mean())

    return tasa_real, meta_tasa


def build_delta_text(actual: float, meta: float) -> str:
    """Construye un texto de delta respecto a la meta (tasa vs tasa)."""
    if meta == 0:
        return "Sin meta"
    diff = actual - meta
    perc = diff / meta * 100
    arrow = "↑" if diff > 0 else "↓"
    return f"{arrow} {perc:,.1f}% vs meta"


# ============================================================
# 3. TAB 1 - Dashboard descriptivo
# ============================================================

def dashboard_tab(df_integrated: pd.DataFrame, mandatos: pd.DataFrame) -> None:
    """Construye la pestaña principal del dashboard descriptivo."""
    st.subheader("📊 Dashboard de Seguridad Ciudadana - Santander")

    # ---------------------------
    # Filtros en sidebar
    # ---------------------------
    with st.sidebar:
        st.header("Filtros")

        # Rango de años tipo "between" (Año inicial / Año final)
        years = sorted(int(y) for y in mandatos["anio"].dropna().unique())
        default_year = 2025 if 2025 in years else max(years)

        col_y1, col_y2 = st.columns(2)
        with col_y1:
            year_from = st.selectbox(
                "Año inicial",
                options=years,
                index=years.index(default_year),
            )
        with col_y2:
            year_to = st.selectbox(
                "Año final",
                options=years,
                index=years.index(default_year),
            )

        # En caso de que el usuario elija un año inicial > año final, lo corregimos
        if year_from > year_to:
            year_from, year_to = year_to, year_from
            st.info(
                "El año inicial era mayor que el año final, "
                "se han intercambiado para mantener un rango válido."
            )


        # Subconjunto de datos para construir listas de filtros
        df_range = df_integrated[
            (df_integrated["anio"] >= year_from)
            & (df_integrated["anio"] <= year_to)
        ].copy()

        # Municipios con opción "Todos"
        municipalities_available = sorted(df_range["municipio"].dropna().unique())
        muni_options = ["Todos"] + municipalities_available
        muni_sel_raw = st.multiselect(
            "Municipios",
            options=muni_options,
            default=["Todos"],
        )
        if "Todos" in muni_sel_raw or not muni_sel_raw:
            muni_selected = municipalities_available
        else:
            muni_selected = muni_sel_raw

        # Delitos con opción "Todos"
        crimes_available = sorted(df_range["delito"].dropna().unique())
        crime_options = ["Todos"] + crimes_available
        crime_sel_raw = st.multiselect(
            "Tipos de delito",
            options=crime_options,
            default=["Todos"],
        )
        if "Todos" in crime_sel_raw or not crime_sel_raw:
            crime_selected = crimes_available
        else:
            crime_selected = crime_sel_raw

    # Aplicar filtros globales
    mask = (df_integrated["anio"] >= year_from) & (df_integrated["anio"] <= year_to)
    if muni_selected:
        mask &= df_integrated["municipio"].isin(muni_selected)
    if crime_selected:
        mask &= df_integrated["delito"].isin(crime_selected)

    df_f = df_integrated[mask].copy()

    if df_f.empty:
        st.warning("No hay datos para la combinación de filtros seleccionada.")
        return

    # Texto de mandatos en rango
    mandatos_range = mandatos[
        (mandatos["anio"] >= year_from) & (mandatos["anio"] <= year_to)
    ]
    mandatos_list = mandatos_range["mandato"].dropna().unique().tolist()
    mandatos_str = ", ".join(mandatos_list) if mandatos_list else "Sin mandato registrado"

    st.markdown(
        f"### Mandatos en rango **{year_from}–{year_to}**: {mandatos_str}"
    )

    # ---------------------------
    # KPIs generales
    # ---------------------------
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    with col_kpi1:
        total_cases = int(df_f["cantidad"].sum())
        st.metric(
            "Total de casos (todas las categorías)",
            f"{total_cases:,}".replace(",", "."),
        )

    with col_kpi2:
        n_municipios = df_f["codigo_municipio"].nunique()
        st.metric("Municipios con registros", n_municipios)

    with col_kpi3:
        total_pop = int(df_f["n_poblacion"].fillna(0).sum())
        st.metric("Población cubierta (suma municipios–años)", f"{total_pop:,}".replace(",", "."))

    st.markdown("---")

    # ---------------------------
    # KPIs por delito vs meta (tasa)
    # ---------------------------
    st.markdown("### Metas departamentales vs realidad (tasa por 100.000 hab.)")

    # Homicidios
    hom_rate, hom_meta = crime_rate_and_meta(df_f, "HOMICIDIOS", "meta_homicidios")

    # Hurtos (distintos alias posibles)
    hurto_aliases = ["HURTOS", "HURTO", "HURTO_PERSONAS"]
    hurto_rate, hurto_meta = crime_rate_and_meta(df_f, hurto_aliases, "meta_hurtos")

    # Lesiones
    lesions_rate, lesions_meta = crime_rate_and_meta(df_f, "LESIONES", "meta_lesiones")

    kpi_cols = st.columns(3)

    with kpi_cols[0]:
        st.metric(
            "Homicidios (tasa vs meta)",
            f"{hom_rate:,.2f}",
            delta=build_delta_text(hom_rate, hom_meta),
        )

    with kpi_cols[1]:
        st.metric(
            "Hurtos (tasa vs meta)",
            f"{hurto_rate:,.2f}",
            delta=build_delta_text(hurto_rate, hurto_meta),
        )

    with kpi_cols[2]:
        st.metric(
            "Lesiones (tasa vs meta)",
            f"{lesions_rate:,.2f}",
            delta=build_delta_text(lesions_rate, lesions_meta),
        )

    st.markdown("---")

    # ---------------------------
    # Gráficas principales
    # ---------------------------

    # Distribución por municipio
    st.markdown("### Distribución de casos por municipio")

    df_muni = (
        df_f.groupby("municipio", as_index=False)["cantidad"]
        .sum()
        .sort_values("cantidad", ascending=False)
    )

    chart_muni = (
        alt.Chart(df_muni)
        .mark_bar()
        .encode(
            x=alt.X("cantidad:Q", title="Número de casos"),
            y=alt.Y("municipio:N", sort="-x", title="Municipio"),
            tooltip=["municipio", "cantidad"],
        )
        .properties(height=400)
    )
    st.altair_chart(chart_muni, use_container_width=True)

    st.markdown("---")

    # Distribución por tipo de delito
    st.markdown("### Distribución por tipo de delito")

    df_crime = (
        df_f.groupby("delito", as_index=False)["cantidad"]
        .sum()
        .sort_values("cantidad", ascending=False)
    )

    chart_crime = (
        alt.Chart(df_crime)
        .mark_bar()
        .encode(
            x=alt.X("cantidad:Q", title="Número de casos"),
            y=alt.Y("delito:N", sort="-x", title="Delito"),
            tooltip=["delito", "cantidad"],
        )
        .properties(height=400)
    )
    st.altair_chart(chart_crime, use_container_width=True)

    st.markdown("---")

    # ---------------------------
    # NUEVO: Evolución mensual dentro del rango
    # ---------------------------
    st.markdown("### Evolución mensual dentro del rango de años seleccionado")

    df_month = (
        df_f.groupby(["anio", "mes"], as_index=False)["cantidad"]
        .sum()
        .sort_values(["anio", "mes"])
    )

    chart_month = (
        alt.Chart(df_month)
        .mark_line(point=True)
        .encode(
            x=alt.X("mes:O", title="Mes"),
            y=alt.Y("cantidad:Q", title="Casos"),
            color=alt.Color("anio:N", title="Año"),
            tooltip=["anio", "mes", "cantidad"],
        )
        .properties(height=350)
    )
    st.altair_chart(chart_month, use_container_width=True)

    st.markdown("---")

    # Tendencia histórica global (todos los años) para los filtros de municipio/delito
    st.markdown("### Tendencia histórica global (todos los años)")

    mask_hist = np.ones(len(df_integrated), dtype=bool)
    if crime_selected:
        mask_hist &= df_integrated["delito"].isin(crime_selected)
    if muni_selected:
        mask_hist &= df_integrated["municipio"].isin(muni_selected)

    df_hist = (
        df_integrated[mask_hist]
        .groupby("anio", as_index=False)["cantidad"]
        .sum()
        .sort_values("anio")
    )

    chart_hist = (
        alt.Chart(df_hist)
        .mark_line(point=True)
        .encode(
            x=alt.X("anio:O", title="Año"),
            y=alt.Y("cantidad:Q", title="Casos totales"),
            tooltip=["anio", "cantidad"],
        )
        .properties(height=350)
    )
    st.altair_chart(chart_hist, use_container_width=True)

    st.markdown("---")

    st.markdown("### Detalle de registros (muestra)")
    st.dataframe(df_f.head(200))


# ============================================================
# 4. TAB 2 - Chatbot / Agente de datos
# ============================================================
# ⚠️ NO SE MODIFICA NADA DE ESTA SECCIÓN
# (solo se alimenta del nuevo df_integrated)
# ============================================================

def explain_stats_agent(df: pd.DataFrame, question: str) -> str:
    """
    Agente basado en Gemini 1.5 Flash que:
        - Recibe el dataframe (contexto resumido) y la pregunta.
        - Genera una respuesta en lenguaje natural usando la API de Google.
    """
    if not GOOGLE_API_KEY:
        return "Error: No hay API Key configurada. Por favor revisa el archivo .env."

    # 1. Preparar contexto de los datos
    # Para no saturar el contexto, enviamos un resumen estadístico y la estructura
    df = normalize_columns(df)
    
    # Rango de años
    min_year = int(df["anio"].min())
    max_year = int(df["anio"].max())
    
    # Totales por delito (top 10)
    top_delitos = df.groupby("delito")["cantidad"].sum().sort_values(ascending=False).head(10).to_dict()
    
    # Totales por municipio (top 10)
    top_muni = df.groupby("municipio")["cantidad"].sum().sort_values(ascending=False).head(10).to_dict()
    
    # Muestra de datos (primeras 5 filas como csv string)
    sample_csv = df.head(5).to_csv(index=False)
    
    # Estructura de columnas
    columns_info = list(df.columns)

    context_prompt = f"""
    Actúa como un experto analista de seguridad ciudadana en Santander, Colombia.
    Tienes acceso a un dataset con las siguientes características:
    
    - Columnas: {columns_info}
    - Rango de años: {min_year} a {max_year}
    - Top 10 Delitos (total histórico): {top_delitos}
    - Top 10 Municipios (total histórico): {top_muni}
    
    Muestra de los datos (CSV):
    {sample_csv}
    
    Instrucciones:
    1. Responde a la pregunta del usuario basándote en la estructura de los datos y los resúmenes proporcionados.
    2. Si la pregunta requiere un cálculo específico que no tienes en el resumen (ej. "cuántos hurtos hubo en 2023 en Bucaramanga"), explica qué pasos lógicos harías o da una estimación basada en tu conocimiento general si es coherente, pero aclara que estás analizando los datos disponibles. 
    3. IMPORTANTE: Si la pregunta es sobre rutas de atención, emergencias o denuncias, SIEMPRE incluye la siguiente información de contacto al final:
       - Emergencias: Línea 123.
       - Violencia intrafamiliar/sexual: Comisarías de Familia, Línea 155.
       - Denuncias: Fiscalía General de la Nación.
    4. Sé amable, claro y conciso.
    
    Pregunta del usuario: "{question}"
    """

    try:
        print(f"DEBUG: Enviando prompt a Gemini... Modelo: gemini-2.0-flash-lite")
        # Usamos el modelo flash como se solicitó
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        response = model.generate_content(context_prompt)
        print(f"DEBUG: Respuesta recibida. Longitud: {len(response.text)}")
        return response.text
    except Exception as e:
        print(f"DEBUG: Error en Gemini: {e}")
        return f"Ocurrió un error al consultar a Gemini: {str(e)}"


def chatbot_tab(df_integrated: pd.DataFrame) -> None:
    """Pestaña de chatbot/agente de datos."""
    st.subheader("🤖 Chat comunitario de datos y rutas de atención")

    st.markdown(
        """
Este chatbot funciona como un **agente sobre los datos**:  
lee tu pregunta, filtra el dataset y genera un resumen estadístico
junto con rutas de atención.

Ejemplos de preguntas:

- *"¿Cómo están los homicidios en Bucaramanga en 2022?"*  
- *"¿Qué pasa con los hurtos en Santander el último año?"*  
- *"¿Cómo van los delitos sexuales en el departamento?"*
"""
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Historial
    with st.container():
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"**Tú:** {msg['content']}")
            else:
                st.markdown(f"**Asistente:** {msg['content']}")

    question = st.text_input("Escribe tu pregunta:", value="", max_chars=300)

    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        if st.button("Enviar", type="primary") and question.strip():
            st.session_state.chat_history.append(
                {"role": "user", "content": question}
            )
            answer = explain_stats_agent(df_integrated, question)
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )
            st.rerun()

    with col_btn2:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.chat_history = []
            st.rerun()


# ============================================================
# 5. MODELOS PREDICTIVOS / ANALÍTICA AVANZADA
# ============================================================
# ⚠️ ESTA SECCIÓN QUEDA IGUAL (solo se alimenta del nuevo df_integrated)
# ============================================================

MODEL_DIR = Path("data/model")


@st.cache_data(show_spinner=True)
def load_model_datasets() -> dict:
    files = {
        "classification_dominant": "classification_dominant_dataset.parquet",
        "classification_event": "classification_event_dataset.parquet",
        "classification_monthly": "classification_monthly_dataset.parquet",
        "clustering_geo": "clustering_geo_dataset.parquet",
        "regression_annual": "regression_annual_dataset.parquet",
        "regression_monthly": "regression_monthly_dataset.parquet",
        "regression_timeseries": "regression_timeseries_dataset.parquet",
    }

    datasets: dict[str, pd.DataFrame | None] = {}
    for key, fname in files.items():
        path = MODEL_DIR / fname
        if path.exists():
            datasets[key] = pd.read_parquet(path)
        else:
            datasets[key] = None
    return datasets


def simple_baseline_prediction(
    df: pd.DataFrame,
    municipio: str,
    delito: str,
    target_year: int,
) -> tuple[float | None, str | pd.DataFrame]:
    df = df.copy()

    df_f = df[(df["municipio"] == municipio) & (df["delito"] == delito)].copy()
    if df_f.empty:
        return None, "No hay datos históricos para ese municipio y delito."

    df_hist = df_f[df_f["anio"] < target_year]
    if df_hist.empty:
        return None, "No hay años anteriores al objetivo para calcular un promedio."

    df_agg = (
        df_hist.groupby("anio", as_index=False)["cantidad"]
        .sum()
        .sort_values("anio")
    )

    pred = float(df_agg["cantidad"].tail(3).mean())
    detalle = df_agg.rename(columns={"anio": "Año", "cantidad": "Casos"})

    return pred, detalle


def prediction_tab(df_integrated: pd.DataFrame) -> None:
    st.subheader("🔮 Módulos predictivos y datasets de modelado")

    ml_data = load_model_datasets()

    st.markdown(
        """
Esta sección organiza los datasets de modelado que vas a usar:

- **Clasificación** (dominante, evento a evento, riesgo mensual)
- **Regresión** (anual, mensual)
- **Series de tiempo** (forecast puro)
- **Clustering geoespacial**

Por ahora actúa como **explorador y documentación viva** de tus datasets.
Cuando tengas los modelos entrenados, aquí mismo podrás conectarlos.
"""
    )

    module = st.radio(
        "Selecciona el módulo a explorar",
        [
            "Clasificación – Delito / arma dominante (dominant_dataset)",
            "Clasificación – Evento a evento (event_dataset)",
            "Clasificación – Riesgo mensual (monthly_dataset)",
            "Regresión – Tendencia anual (annual_dataset)",
            "Regresión – Forecast mensual (monthly_dataset)",
            "Series de tiempo – Forecast puro (timeseries_dataset)",
            "Clustering geoespacial-delictivo (geo_dataset)",
        ],
        index=4,
    )

    def show_dataset_info(df: pd.DataFrame | None, nombre_archivo: str, descripcion: str) -> None:
        st.markdown(f"**Archivo:** `{nombre_archivo}`")
        st.markdown(descripcion)

        if df is None:
            st.warning(
                "⚠️ Aún no encontré este archivo en la carpeta `data/model`. "
                "Cuando lo generes, se cargará automáticamente."
            )
            return

        st.info(f"Filas: **{len(df):,}** – Columnas: **{len(df.columns)}**")
        with st.expander("Ver columnas disponibles"):
            st.write(list(df.columns))

        with st.expander("Vista previa (primeras filas)"):
            st.dataframe(df.head(50))

    if module.startswith("Clasificación – Delito / arma dominante"):
        show_dataset_info(
            ml_data["classification_dominant"],
            "classification_dominant_dataset.parquet",
            """
**Uso previsto:**

- Predicción del **delito dominante** por municipio–año–mes.
- Predicción del **arma/medio dominante**.
- Análisis de municipios que cambian de delito dominante en el tiempo.
""",
        )

    elif module.startswith("Clasificación – Evento a evento"):
        show_dataset_info(
            ml_data["classification_event"],
            "classification_event_dataset.parquet",
            """
**Uso previsto:**

- Clasificación multiclase a nivel de **evento delictivo**.
- Predicción del tipo de delito y/o perfil (agresor, víctima).
- Probabilidad de ocurrencia según contexto (fecha, municipio, demografía).
""",
        )

    elif module.startswith("Clasificación – Riesgo mensual"):
        show_dataset_info(
            ml_data["classification_monthly"],
            "classification_monthly_dataset.parquet",
            """
**Uso previsto:**

- Clasificación de **riesgo mensual** (Bajo / Medio / Alto) por municipio.
- Clasificación binaria (incremento / no incremento).
""",
        )

    elif module.startswith("Regresión – Tendencia anual"):
        show_dataset_info(
            ml_data["regression_annual"],
            "regression_annual_dataset.parquet",
            """
**Uso previsto:**

- Modelos de **regresión anual** por municipio.
- Predicción de delitos anuales y tendencias a largo plazo.
""",
        )

    elif module.startswith("Regresión – Forecast mensual"):
        show_dataset_info(
            ml_data["regression_monthly"],
            "regression_monthly_dataset.parquet",
            """
**Uso previsto:**

- Regresión mensual pura con lags, ventanas móviles y estacionalidad.
- Predicción del número **exacto** de delitos el próximo mes.
""",
        )

    elif module.startswith("Series de tiempo – Forecast puro"):
        show_dataset_info(
            ml_data["regression_timeseries"],
            "regression_timeseries_dataset.parquet",
            """
**Uso previsto:**

- Modelos clásicos de series de tiempo (ARIMA, Prophet, LSTMs, etc.).
- Forecast mes a mes con foco total en la dinámica temporal.
""",
        )

    elif module.startswith("Clustering geoespacial-delictivo"):
        show_dataset_info(
            ml_data["clustering_geo"],
            "clustering_geo_dataset.parquet",
            """
**Uso previsto:**

- Clustering geoespacial–delictivo (KMeans, HDBSCAN, etc.).
- Agrupación de municipios según perfil delictivo, demografía y geografía.
""",
        )

    st.markdown("---")
    st.subheader("🧪 Baseline histórico rápido (demo de predicción)")

    df = df_integrated.copy()

    municipios = sorted(df["municipio"].dropna().unique())
    delitos = sorted(df["delito"].dropna().unique())

    col1, col2 = st.columns(2)
    with col1:
        muni_sel = st.selectbox("Municipio", municipios)
    with col2:
        delito_sel = st.selectbox("Tipo de delito", delitos)

    year_min = int(df["anio"].min())
    year_max = int(df["anio"].max())

    target_year = st.number_input(
        "Año a predecir (baseline)",
        min_value=year_max + 1,
        max_value=year_max + 10,
        value=year_max + 1,
        step=1,
    )

    if st.button("Calcular predicción baseline", type="primary"):
        pred, detail = simple_baseline_prediction(
            df,
            municipio=muni_sel,
            delito=delito_sel,
            target_year=target_year,
        )
        if pred is None:
            st.warning(str(detail))
        else:
            st.success(
                f"Predicción baseline para **{muni_sel}**, delito **{delito_sel}** "
                f"en el año **{target_year}**"
            )
            st.metric("Casos estimados (promedio últimos 3 años)", f"{pred:,.0f}")
            st.markdown("**Histórico usado para el cálculo:**")
            st.dataframe(detail.tail(5))


# ============================================================
# 6. MAIN
# ============================================================

def main() -> None:
    st.title("Tablero Inteligente de Seguridad Ciudadana - Santander")

    try:
        data = load_base_tables()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Error cargando los datos: {exc}")
        st.stop()

    metas = data["metas"]
    mandatos = data["mandatos"]
    poblacion = data["poblacion"]
    policia = data["policia"]
    municipios = data["municipios"]
    delitos_bucaramanga = data["delitos_bucaramanga"]
    delitos_informaticos = data["delitos_informaticos"]

    df_integrated = build_integrated_df(
        metas,
        mandatos,
        poblacion,
        policia,
        municipios,
        delitos_bucaramanga,
        delitos_informaticos,
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "📊 Dashboard",
            "🤖 Chatbot comunitario",
            "🔮 Modelo predictivo",
        ]
    )

    with tab1:
        dashboard_tab(df_integrated, mandatos)

    with tab2:
        chatbot_tab(df_integrated)

    with tab3:
        prediction_tab(df_integrated)


if __name__ == "__main__":
    main()

