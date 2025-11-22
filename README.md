# 📊 Datos al Ecosistema - Reto Intermedio: Seguridad en Santander

Este repositorio contiene el desarrollo de la solución para el reto **"Datos al Ecosistema"**, enfocado en el análisis y modelado de datos de seguridad y convivencia en el departamento de Santander.

| Sección | Descripción |
| :--- | :--- |
| [👥 Equipo](#equipo) | Miembros del equipo de desarrollo. |
| [🎯 Objetivos generales](#objetivos-generales) | Visión general del plan de 6 etapas. |
| [📂 Estructura General](#estructura-general) | Arquitectura de datos y modelo predictivo. |
| [🚀 Qué estamos haciendo](#qué-estamos-haciendo) | Detalle de las etapas 1 y 2 (Ingeniería de Datos). |

## 👥 Equipo

Somos un equipo de **4 integrantes** comprometidos con el uso de datos para el impacto social:
- Alejandra Uribe Sierra 
- Shorly López Pérez
- Mateo Arenas Montoya
- Sergio Luis López Verbel

## 🎯 Objetivos generales

Para abordar el reto, hemos diseñado un plan de trabajo general compuesto por 6 etapas:

1.  **Recopilación de fuentes de datos.**
2.  **Creación de infraestructura de datos, limpieza y modelado.**
3.  Diseño de Dashboard.
4.  Creación de modelos predictivos.
5.  Desarrollo del Chatbot.
6.  Documentación, validación y entrega.

**Este repositorio se centra específicamente en el desarrollo de los pasos 1 y 2**: la construcción de un **Data Lake** robusto (desde la ingesta hasta la capa Oro) y la preparación de la infraestructura necesaria para el posterior análisis y modelado.

## 📂 Estructura General

El proyecto sigue una arquitectura de medallón (Medallion Architecture) para el manejo de datos:

*   **Bronze**: Datos crudos tal como llegan de la fuente.
*   **Silver**: Datos limpios, validados y estandarizados.
*   **Gold**: Datos agregados y listos para reportes o IA.

Además, se implementa un modelo predictivo para predecir comportamientos delictivos.

## 🚀 ¿Qué estamos haciendo?

Actualmente, el repositorio centraliza todo el flujo de ingeniería de datos, desde la obtención de la información hasta su preparación para el análisis avanzado.

Nuestro flujo de trabajo se divide en:

1.  **Ingesta de Datos (Capa Bronze)**: Recopilación automática de datos desde múltiples fuentes oficiales:
    *   **Policía Nacional**: Estadísticas delictivas (Web Scraping y descargas).
    *   **Datos Abiertos (Socrata)**: Datasets gubernamentales.
    *   **DANE**: Información geográfica y de división política (Divipola).
2.  **Procesamiento y Limpieza (Capa Silver)**: Estandarización, limpieza y estructuración de los datos para asegurar su calidad.
3.  **Modelado y Enriquecimiento (Capa Gold - *En progreso*)**: Integración geoespacial (Policía + DANE) y agregación de datos para Dashboards.
4.  **Modelado Predictivo (*Próximamente*)**: Desarrollo de modelos de regresión (volumen delictivo) y clasificación (tipo de delito).
