# 📘 Detalle Técnico y Estado del Proyecto

Este documento detalla el estado actual del desarrollo técnico, la arquitectura de datos implementada y los siguientes pasos para completar el reto.

| Sección | Descripción |
| :--- | :--- |
| [📍 Estado Actual](#estado-actual) | Resumen de progreso por capas (Bronze/Silver/Gold). |
| [🛠️ Arquitectura](#arquitectura) | Explicación técnica de los scripts y procesos. |
| [🚀 Roadmap](#roadmap) | Pasos futuros inmediatos. |
| [🔍 Detalle Técnico del Roadmap](#detalle-tecnico-del-roadmap) | Explicación profunda de Joins, Agregaciones y Features. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[1. Construcción de la Capa Gold](#construccion-gold) | Detalles sobre Joins y Agregaciones. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[2. Feature Engineering](#feature-engineering) | Variables temporales y lags. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[3. Modelado Predictivo](#modelado-predictivo) | Mock model, regresión y clasificación. |
| [❓ FAQ](#faq) | Definiciones de conceptos clave como Parquet. |


<a id="estado-actual"></a>
## 📍 Estado Actual: ¿En qué vamos?

**Resumen**: Hemos completado exitosamente la **Capa Bronze (Ingesta)** y la **Capa Silver (Limpieza y Estandarización)** para nuestras fuentes de datos principales (Policía Nacional y DANE).

Actualmente, el proyecto se encuentra listo para iniciar la construcción de la **Capa Gold**, donde uniremos los datos delictivos con la información geográfica para habilitar el modelado.

| Capa | Estado | Descripción |
| :--- | :--- | :--- |
| **Bronze** | ✅ Completado | Datos crudos descargados (Excel, JSON, GeoJSON). |
| **Silver** | ✅ Completado | Datos limpios, normalizados y convertidos a **Parquet**. |
| **Gold** | 🚧 Pendiente | Enriquecimiento, cruce de datos y tabla maestra para el modelo. |
| **Modelo** | ⏳ Pendiente | Entrenamiento del modelo predictivo. |


<a id="arquitectura"></a>
## 🛠️ Arquitectura y Flujo de Datos

### 1. Capa Bronze: Ingesta de Datos
En esta etapa, traemos los datos "tal cual" existen en las fuentes oficiales.

*   **Fuentes de Datos**:
    *   **Policía Nacional (Estadística Delictiva)**:
        *   *Script*: `01_scrape_policia_estadistica.py` y `01_extract_bronze.py`.
        *   *Técnica*: Web Scraping avanzado. El script navega por la página de la policía, identifica los archivos de Excel históricos y del año actual (2025), y los descarga.
        *   *Reto superado*: La página de la policía usa visores de Office en línea para 2025; el script es capaz de extraer la URL real de descarga de estos visores.
    *   **Datos Abiertos (Socrata API)**:
        *   *Script*: `01_extract_bronze.py`.
        *   *Técnica*: Conexión vía API (Socrata) para descargar datasets específicos como "Hurto a residencias" o "Violencia intrafamiliar" en formato JSON.
    *   **DANE (Geografía)**:
        *   *Script*: `01_generate_polygon_santander.py`.
        *   *Técnica*: Descarga de la cartografía oficial de Colombia (GeoJSON) y filtrado específico para el departamento de **Santander**.

### 2. Capa Silver: Limpieza y Estandarización
Aquí es donde ocurre la "magia" de la calidad de datos. Transformamos archivos de Excel desordenados en tablas estructuradas de alto rendimiento.

*   **Procesamiento de Policía (`02_process_silver_policia.py`)**:
    *   **Unificación**: El script toma docenas de archivos Excel (uno por año y tipo de delito) y los fusiona en una sola tabla.
    *   **Normalización de Columnas**: Los archivos originales cambian de nombres de columnas con los años (ej: "EDAD", "RANGO EDAD", "AGRUPA EDAD"). El script detecta estas variaciones y las unifica en una sola columna estándar (`edad_persona`).
    *   **Limpieza de Valores**: Se estandarizan textos (mayúsculas, sin tildes) y se manejan valores nulos como "NO REPORTADO".
    *   **Filtrado**: Se filtra exclusivamente para el departamento de **SANTANDER**.

*   **Procesamiento Geográfico (`02_process_silver_danegeo.py`)**:
    *   **Divipola**: Se limpia el listado de municipios del DANE para tener códigos oficiales estandarizados.
    *   **GeoJSON**: Se optimiza el archivo de polígonos de los municipios para que sea ligero y compatible.


<a id="roadmap"></a>
## 🚀 Siguientes Pasos (Roadmap)

Para llegar al objetivo final, estos son los pasos que siguen:

1.  **Construir la Capa Gold**:
    *   **Unión de Tablas (Joins)**: Cruzar `policia` con `divipola` y luego con `geografia` para obtener la ubicación exacta.
    *   **Agregación**: Crear tablas resumen para el **Dashboard** (ej: delitos por mes/municipio).

2.  **Ingeniería de Características (Feature Engineering)**:
    *   Crear variables para el modelo (lags, fechas, etc.).

3.  **Modelado Predictivo**:
    *   Crear un **Mock Model** para pruebas de despliegue.
    *   Entrenar modelos de **Regresión** (cantidad de delitos) y **Clasificación** (tipo de delito).

<a id="detalle-tecnico-del-roadmap"></a>
## 🔍 Siguientes Pasos en Detalle

A continuación, explicamos en profundidad la estrategia técnica para las próximas etapas.

<a id="construccion-gold"></a>
### 1. Construcción de la Capa Gold

Esta etapa es crítica para habilitar tanto el Dashboard como el Modelo.

**a. Unión de Tablas (Joins)**
Necesitamos conectar los delitos con la información geográfica oficial. La lógica de unión será la siguiente:

1.  **Origen**: `policia_santander.parquet` (tiene `codigo_dane` del municipio).
2.  **Puente**: `divipola_silver.parquet` (tiene `codigo_centro_poblado` y `codigo_municipio`).
3.  **Destino**: `geografia_silver.parquet` (tiene la geometría asociada al `codigo_municipio`).

*   **Reto Técnico**: No perder la geometría durante el cruce.
*   **Solución**: Usaremos **GeoPandas** (o alguna otra librería geográfica) para manejar el GeoDataFrame final.

**b. Agregación de Datos**
El objetivo aquí es preparar tablas optimizadas para el **Dashboard**. Los datos crudos son demasiado granulares.
*   **Ejemplo**: Agrupar por `municipio`, `anio`, `mes` y `delito` para visualizar tendencias.

<a id="feature-engineering"></a>
### 2. Ingeniería de Características (Feature Engineering)
Preparación exclusiva para el modelo de IA.
*   **Variables Temporales**: Día de la semana, festivos, quincena.
*   **Lags (Rezagos)**: Cantidad de delitos del mes anterior (clave para series de tiempo).

<a id="modelado-predictivo"></a>
### 3. Modelado Predictivo
Nuestro objetivo inmediato es tener un **Mock Model** (modelo base) para probar el flujo de despliegue:

**a. Predicción de Demanda (Regresión)**
*   *Pregunta*: ¿Cuántos delitos ocurrirán en el municipio X la próxima semana?
*   *Variables*: Municipio, Fecha, Sexo.

**b. Clasificación de Riesgo**
*   *Pregunta*: Dadas las características (lugar, hora), ¿qué tipo de delito es más probable?
*   *Variables*: Municipio, Fecha, Hora.

<a id="faq"></a>
## ❓ FAQ (Conceptos Generales)

### 💡 ¿Qué es Parquet y por qué lo usamos?
En la capa Silver, guardamos los datos en formato **Parquet** (ej: `policia_santander.parquet`).
*   **¿Qué es?**: Es un formato de almacenamiento de datos "columnar" (guarda los datos por columnas, no por filas).
*   **Ventajas**:
    *   **Compresión**: Ocupa mucho menos espacio que un Excel o CSV (hasta 10 veces menos).
    *   **Velocidad**: Permite leer los datos muchísimo más rápido, ideal para cuando tengamos millones de registros de delitos.
    *   **Tipos de Datos**: Mantiene la información de si una columna es número o fecha, evitando errores de conversión.

---