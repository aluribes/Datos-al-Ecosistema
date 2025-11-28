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

Simula el modelo relacional uniéndolas en memoria para:

    - Dashboard descriptivo
    - Chat de datos (agente sencillo)
    - Modelo predictivo baseline (promedio histórico)
"""

from pathlib import Path
from typing import Dict, List, Tuple

import altair as alt
import pandas as pd
import streamlit as st

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

    # Normalizar nombres de columnas (quitar espacios)
    for df in (metas, mandatos, poblacion, policia, municipios):
        df.columns = [c.strip() for c in df.columns]

    return {
        "metas": metas,
        "mandatos": mandatos,
        "poblacion": poblacion,
        "policia": policia,
        "municipios": municipios,
    }


def build_integrated_df(
    metas: pd.DataFrame,
    mandatos: pd.DataFrame,
    poblacion: pd.DataFrame,
    policia: pd.DataFrame,
    municipios: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construye un DataFrame integrado a nivel de hecho policial,
    uniendo policia + municipios + población + mandatos + metas.
    """
    df = policia.copy()

    # Join dimensión espacial (municipios)
    df = df.merge(
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
        suffixes=("", "_muni"),
    )

    # Join población (para tasas)
    df = df.merge(
        poblacion[["codigo_municipio", "anio", "n_poblacion"]],
        on=["codigo_municipio", "anio"],
        how="left",
    )

    # Join mandatos y metas
    df = df.merge(mandatos, on="anio", how="left")  # agrega "mandato"
    df = df.merge(metas, on="mandato", how="left")  # agrega metas y presupuesto

    # Calcular tasa por 100.000 habitantes
    df["tasa_100k"] = df["cantidad"] / df["n_poblacion"] * 1e5

    # Tipos básicos y normalización
    df["anio"] = df["anio"].astype(int)
    df["delito"] = df["delito"].astype(str).str.upper()
    df["municipio"] = df["municipio"].astype(str).str.upper()

    return df


# ============================================================
# 2. Helpers genéricos (normalización y agregaciones)
# ============================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas (strip) y retorna copia."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df


def aggregate_delito(
    df: pd.DataFrame,
    crime_name: str,
    meta_col: str,
) -> Tuple[int, float]:
    """
    Agrega casos y meta a nivel departamental para un delito concreto.
    Devuelve (casos_totales, meta_anual).
    """
    df_crime = df[df["delito"] == crime_name].copy()
    cases = int(df_crime["cantidad"].sum()) if not df_crime.empty else 0

    meta = 0.0
    if meta_col in df_crime.columns and not df_crime[meta_col].dropna().empty:
        meta = float(df_crime[meta_col].dropna().iloc[0])

    return cases, meta


def build_delta_text(actual: int, meta: float) -> str:
    """Construye un texto de delta respecto a la meta."""
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

        years = sorted(mandatos["anio"].unique())
        year_selected = st.selectbox("Año de mandato", years, index=len(years) - 1)

        mandatos_sel = mandatos.loc[
            mandatos["anio"] == year_selected, "mandato"
        ].unique()
        mandato_selected = mandatos_sel[0] if len(mandatos_sel) > 0 else None

        df_year = df_integrated[df_integrated["anio"] == year_selected].copy()

        municipalities_available = sorted(df_year["municipio"].dropna().unique())
        muni_selected = st.multiselect(
            "Municipios",
            options=municipalities_available,
            default=municipalities_available,
        )

        crimes_available = sorted(df_year["delito"].dropna().unique())
        crime_selected = st.multiselect(
            "Tipos de delito",
            options=crimes_available,
            default=crimes_available,
        )

    # Aplicar filtros
    mask = df_integrated["anio"] == year_selected
    if muni_selected:
        mask &= df_integrated["municipio"].isin(muni_selected)
    if crime_selected:
        mask &= df_integrated["delito"].isin(crime_selected)

    df_f = df_integrated[mask].copy()

    if df_f.empty:
        st.warning("No hay datos para la combinación de filtros seleccionada.")
        return

    # ---------------------------
    # KPIs generales
    # ---------------------------
    st.markdown(f"### Mandato **{mandato_selected}** – Año **{year_selected}**")

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
        st.metric("Población cubierta", f"{total_pop:,}".replace(",", "."))

    st.markdown("---")

    # ---------------------------
    # KPIs por delito vs meta
    # ---------------------------
    st.markdown("### Metas departamentales vs realidad")

    # Homicidios
    hom_cases, hom_meta = aggregate_delito(df_f, "HOMICIDIOS", "meta_homicidios")

    # Hurtos (distintos alias posibles)
    hurto_aliases = ["HURTOS", "HURTO", "HURTO_PERSONAS"]
    hurto_cases = int(df_f[df_f["delito"].isin(hurto_aliases)]["cantidad"].sum())
    hurto_meta = 0.0
    if "meta_hurtos" in df_f.columns and not df_f["meta_hurtos"].dropna().empty:
        hurto_meta = float(df_f["meta_hurtos"].dropna().iloc[0])

    # Lesiones
    lesions_cases, lesions_meta = aggregate_delito(df_f, "LESIONES", "meta_lesiones")

    kpi_cols = st.columns(3)

    with kpi_cols[0]:
        st.metric(
            "Homicidios (casos vs meta)",
            f"{hom_cases:,}".replace(",", "."),
            delta=build_delta_text(hom_cases, hom_meta),
        )

    with kpi_cols[1]:
        st.metric(
            "Hurtos (casos vs meta)",
            f"{hurto_cases:,}".replace(",", "."),
            delta=build_delta_text(hurto_cases, hurto_meta),
        )

    with kpi_cols[2]:
        st.metric(
            "Lesiones (casos vs meta)",
            f"{lesions_cases:,}".replace(",", "."),
            delta=build_delta_text(lesions_cases, lesions_meta),
        )

    st.markdown("---")

    # ---------------------------
    # Gráfico: distribución por municipio
    # ---------------------------
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

    # ---------------------------
    # Gráfico: distribución por tipo de delito
    # ---------------------------
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
    # Tendencia histórica (todos los años)
    # ---------------------------
    st.markdown("### Tendencia histórica (todos los años)")

    mask_hist = df_integrated["delito"].isin(crime_selected) if crime_selected else True
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

def explain_stats_agent(df: pd.DataFrame, question: str) -> str:
    """
    Agente sencillo que:
        - Detecta delito, municipio y año (si se menciona).
        - Calcula casos y tasa.
        - Explica en lenguaje natural y añade rutas de atención.
    """
    df = normalize_columns(df)

    text = question.lower()

    # --- Detectar delito por palabras clave ---
    crime_map = {
        "homicid": "HOMICIDIOS",
        "asesin": "HOMICIDIOS",
        "hurto": "HURTOS",
        "robo": "HURTOS",
        "lesion": "LESIONES",
        "violencia intrafamiliar": "VIOLENCIA INTRAFAMILIAR",
        "intrafamiliar": "VIOLENCIA INTRAFAMILIAR",
        "sexual": "DELITOS SEXUALES",
        "informatic": "DELITOS INFORMÁTICOS",
    }
    crime_detected = None
    for key, crime in crime_map.items():
        if key in text:
            crime_detected = crime
            break

    # --- Detectar municipio buscando coincidencia exacta del nombre ---
    muni_detected = None
    for muni in df["municipio"].dropna().unique():
        if str(muni).lower() in text:
            muni_detected = muni
            break

    # --- Detectar año (si hay un número de 4 dígitos en rango) ---
    year_detected = None
    years_valid = df["anio"].unique().tolist()
    for token in text.split():
        if token.isdigit() and len(token) == 4:
            year_candidate = int(token)
            if year_candidate in years_valid:
                year_detected = year_candidate
                break

    if year_detected is None:
        year_detected = int(df["anio"].max())

    # --- Construir filtro ---
    df_q = df[df["anio"] == year_detected].copy()
    filtros_txt: List[str] = [f"año = **{year_detected}**"]

    if crime_detected is not None:
        df_q = df_q[df_q["delito"] == crime_detected]
        filtros_txt.append(f"delito = **{crime_detected}**")

    if muni_detected is not None:
        df_q = df_q[df_q["municipio"] == muni_detected]
        filtros_txt.append(f"municipio = **{muni_detected}**")

    if df_q.empty:
        resumen = (
            "Con la información disponible no encontré registros que coincidan con tu pregunta. "
            "Prueba preguntando solo por tipo de delito o solo por municipio."
        )
    else:
        total_cases = int(df_q["cantidad"].sum())
        tasa_prom = float(df_q["tasa_100k"].mean()) if "tasa_100k" in df_q.columns else None

        # Comparar con año anterior si existe
        trend_text = ""
        prev_year = year_detected - 1
        if prev_year in years_valid:
            df_prev = df[
                (df["anio"] == prev_year)
                & (df_q["delito"].unique().tolist() if crime_detected else [True])
            ].copy()
            if muni_detected is not None:
                df_prev = df_prev[df_prev["municipio"] == muni_detected]

            if not df_prev.empty:
                prev_cases = int(df_prev["cantidad"].sum())
                diff = total_cases - prev_cases
                sign = "más" if diff > 0 else "menos" if diff < 0 else "igual número de"
                trend_text = (
                    f" En comparación con {prev_year}, hay **{abs(diff):,} casos {sign}**."
                    if diff != 0
                    else f" En comparación con {prev_year}, se mantiene un nivel similar de casos."
                )

        filtros_str = ", ".join(filtros_txt)
        if tasa_prom is not None and not pd.isna(tasa_prom):
            resumen = (
                f"Con los filtros {filtros_str}, se registran **{total_cases:,} casos** "
                f"y una **tasa promedio de {tasa_prom:,.2f} por cada 100.000 habitantes**."
            )
        else:
            resumen = (
                f"Con los filtros {filtros_str}, se registran **{total_cases:,} casos** "
                f"(no tengo columna de tasa disponible)."
            )

        if trend_text:
            resumen += trend_text

    rutas = """
**Rutas de atención recomendadas**

- Emergencias y situaciones en curso: **línea 123** (Policía Nacional).
- Violencia intrafamiliar y delitos sexuales:
  - **Comisarías de Familia** del municipio.
  - **Línea 155** (orientación a mujeres).
- Denuncias formales:
  - **Fiscalía General de la Nación** (URI / CAI / Casas de Justicia).
  - Estaciones de Policía más cercanas.

Recuerda que estos datos son estadísticos y no reemplazan las rutas oficiales de atención inmediata.
"""

    return resumen + "\n\n" + rutas


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
            st.experimental_rerun()

    with col_btn2:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.chat_history = []
            st.experimental_rerun()


# ============================================================
# 5. MODELOS PREDICTIVOS / ANALÍTICA AVANZADA
# ============================================================

# Carpeta donde vas a guardar los datasets de modelado
# (ajusta la ruta si los tienes en otro lado)
MODEL_DIR = Path("data/model")


@st.cache_data(show_spinner=True)
def load_model_datasets() -> dict:
    """
    Carga los datasets de modelado (si existen).
    No rompe la app si alguno todavía no está creado.
    """
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
    """
    Baseline muy simple:
        - Usa el dataset integrado (no los datasets de modelado).
        - Toma los últimos 3 años antes del año objetivo.
        - Predicción = promedio de casos de esos 3 años.
    """
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
    """
    Pestaña de modelos predictivos, organizada en dos bloques:

    1. Explorador de datasets de modelado (clasificación, regresión, clustering,
       series de tiempo). Aquí se cargan y se muestran los datasets que
       utilizarán tus futuros modelos.

    2. Baseline histórico simple (ya funcional) que calcula un pronóstico
       usando el dataset integrado actual.
    """
    st.subheader("🔮 Módulos predictivos y datasets de modelado")

    # ----------------------------------------------
    # 5.1 Explorador de datasets de modelado
    # ----------------------------------------------
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
        index=4,  # por defecto: regresión mensual
    )

    # Helper para mostrar info básica de un dataset
    def show_dataset_info(df: pd.DataFrame | None, nombre_archivo: str, descripcion: str) -> None:
        st.markdown(f"**Archivo:** `{nombre_archivo}`")
        st.markdown(descripcion)

        if df is None:
            st.warning("⚠️ Aún no encontré este archivo en la carpeta `data/model`. "
                       "Cuando lo generes, se cargará automáticamente.")
            return

        st.info(f"Filas: **{len(df):,}** – Columnas: **{len(df.columns)}**")
        with st.expander("Ver columnas disponibles"):
            st.write(list(df.columns))

        with st.expander("Vista previa (primeras filas)"):
            st.dataframe(df.head(50))

    # Según el módulo seleccionado, mostramos el dataset correspondiente
    if module.startswith("Clasificación – Delito / arma dominante"):
        show_dataset_info(
            ml_data["classification_dominant"],
            "classification_dominant_dataset.parquet",
            """
**Uso previsto:**

- Predicción del **delito dominante** por municipio–año–mes.
- Predicción del **arma/medio dominante**.
- Análisis de municipios que cambian de delito dominante en el tiempo.

**Preguntas que responde:**

- ¿Cuál será el delito más frecuente el próximo mes?
- ¿Qué arma/medio será más usado?
- ¿Qué municipios cambian su patrón dominante?
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

**Preguntas que responde:**

- ¿Qué tipo de delito es más probable en cierto contexto?
- ¿El perfil asociado se puede predecir?
- ¿Qué factores temporales influyen en cada delito?
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

**Preguntas que responde:**

- ¿Qué municipios están en riesgo alto el próximo mes?
- ¿En qué municipios aumentarán los delitos?
- ¿Qué variables explican mejor el riesgo mensual?

**Utilidad:** Semáforos delictivos y alertas tempranas para el tablero.
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

**Preguntas que responde:**

- ¿Cuál será la cantidad de delitos el próximo año?
- ¿Qué municipios tienen tendencias ascendentes o descendentes?
- ¿Qué factores influyen en la variación anual?

**Utilidad:** Planeación estratégica e informes institucionales.
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

**Preguntas que responde:**

- ¿Cuántos delitos habrá el siguiente mes?
- ¿Cómo varía el volumen a lo largo del año?
- ¿Qué variables explican mejor la fluctuación mensual?

**Utilidad:** Forecast detallado para el tablero y alertas numéricas.
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

**Preguntas que responde:**

- ¿Cómo evolucionarán los delitos mes a mes?
- ¿Existen patrones estacionales fuertes?
- ¿Qué municipios presentan mayor periodicidad?

**Utilidad:** Forecast robusto orientado al tiempo.
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

**Preguntas que responde:**

- ¿Qué municipios se parecen entre sí en su comportamiento?
- ¿Qué grupos presentan mayor concentración de delitos?
- ¿Existen patrones urbano–rural?

**Utilidad:** Políticas diferenciadas por tipo de municipio y mapas de clusters.
""",
        )

    st.markdown("---")
    st.subheader("🧪 Baseline histórico rápido (demo de predicción)")

    # ----------------------------------------------
    # 5.2 Baseline histórico (sigue usando df_integrated)
    # ----------------------------------------------
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

    df_integrated = build_integrated_df(metas, mandatos, poblacion, policia, municipios)

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
