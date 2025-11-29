# Guía de Modelos - Tablero de Seguridad Ciudadana Santander

## Estructura de Modelos

```
models/
├── descriptivo/
│   └── classification_event/     # Estadísticas pre-calculadas
│       ├── resumen_general.json
│       ├── distribucion_delitos.json
│       ├── distribucion_perfiles.json
│       ├── analisis_temporal.json
│       ├── analisis_demografico.json
│       ├── analisis_geografico.json
│       ├── cruces_delito_perfil.json
│       ├── top_combinaciones.json
│       └── respuestas_chatbot.json
│
└── predictivos/
    └── classification_event/     # Modelo Multi-Output
        ├── xgb_multioutput_event.joblib
        ├── label_encoder_delito.joblib
        ├── label_encoder_perfil.joblib
        ├── label_encoder_edad.joblib
        ├── scaler.joblib
        └── metadata.json
```

---

## 1. Modelo Descriptivo

### Finalidad

Proporcionar **estadísticas pre-calculadas** para respuestas rápidas sin necesidad de procesar datos en tiempo real. Ideal para:

- Mostrar KPIs en el dashboard
- Responder preguntas frecuentes del chatbot
- Generar visualizaciones estáticas
- Reducir carga del servidor

### Archivos y Contenido

| Archivo | Contenido | Uso Principal |
|---------|-----------|---------------|
| `resumen_general.json` | Total eventos, período, municipios, tipos de delito | Header del dashboard, intro chatbot |
| `distribucion_delitos.json` | Conteo y % por tipo de delito | Gráficos pie/barras |
| `distribucion_perfiles.json` | Conteo y % por perfil (agresor/víctima) | Filtros, segmentación |
| `analisis_temporal.json` | Datos por año, mes, trimestre, variación anual | Gráficos de tendencia |
| `analisis_demografico.json` | Por grupo etario y género | Análisis de población afectada |
| `analisis_geografico.json` | Top municipios, delitos por zona | Mapas de calor |
| `cruces_delito_perfil.json` | Relación delito-perfil | Heatmaps |
| `top_combinaciones.json` | Combinaciones más frecuentes | Rankings, alertas |
| `respuestas_chatbot.json` | Respuestas pre-generadas | Chatbot |

### Uso en el Tablero Web

```python
import json

# Cargar KPIs para el header
with open('models/descriptivo/classification_event/resumen_general.json') as f:
    resumen = json.load(f)

# Mostrar en dashboard
total_eventos = resumen['total_eventos']
periodo = f"{resumen['periodo']['anio_inicio']} - {resumen['periodo']['anio_fin']}"
n_municipios = resumen['geografia']['n_municipios']

# Cargar distribución para gráfico de barras
with open('models/descriptivo/classification_event/distribucion_delitos.json') as f:
    delitos = json.load(f)

# Datos para gráfico
labels = [d['delito'] for d in delitos['distribucion']]
values = [d['cantidad'] for d in delitos['distribucion']]
```

### Uso en el Chatbot

```python
import json

# Cargar respuestas pre-generadas
with open('models/descriptivo/classification_event/respuestas_chatbot.json') as f:
    respuestas = json.load(f)

def responder_pregunta(pregunta):
    # Buscar en preguntas frecuentes
    for qa in respuestas['preguntas_respuestas']:
        if pregunta.lower() in qa['pregunta'].lower():
            return qa['respuesta']
    
    # Buscar por delito específico
    for delito, info in respuestas['respuestas_por_delito'].items():
        if delito.lower() in pregunta.lower():
            return info['respuesta']
    
    # Buscar por municipio
    for municipio, info in respuestas['respuestas_por_municipio'].items():
        if municipio.lower() in pregunta.lower():
            return info['respuesta']
    
    return "No tengo información sobre esa pregunta."

# Ejemplos
print(responder_pregunta("¿Cuál es el delito más común?"))
print(responder_pregunta("¿Cuántos hurtos hay?"))
print(responder_pregunta("¿Qué pasa en Bucaramanga?"))
```

### Preguntas que Responde

| Pregunta | Archivo a Consultar |
|----------|---------------------|
| ¿Cuántos delitos hay en total? | `resumen_general.json` |
| ¿Cuál es el delito más común? | `distribucion_delitos.json` |
| ¿Cómo varían los delitos por mes? | `analisis_temporal.json` |
| ¿Qué municipio tiene más hurtos? | `analisis_geografico.json` |
| ¿Qué grupo etario es más afectado? | `analisis_demografico.json` |
| ¿Qué perfil domina en violencia intrafamiliar? | `cruces_delito_perfil.json` |

---

## 2. Modelo Predictivo

### Finalidad

Predecir **tipo de delito y perfil** dado un contexto específico. Utiliza Machine Learning (XGBoost Multi-Output) para:

- Anticipar qué delito es más probable en ciertas condiciones
- Predecir si el evento involucra agresor o víctima
- Identificar combinaciones de alto riesgo
- Generar alertas proactivas

### Archivos del Modelo

| Archivo | Contenido |
|---------|-----------|
| `xgb_multioutput_event.joblib` | Modelo XGBoost entrenado |
| `label_encoder_delito.joblib` | Encoder para tipos de delito |
| `label_encoder_perfil.joblib` | Encoder para perfiles |
| `label_encoder_edad.joblib` | Encoder para grupos etarios |
| `scaler.joblib` | StandardScaler para normalizar features |
| `metadata.json` | Info del modelo, métricas, features |

### Features Requeridas

```python
FEATURES = [
    # Temporales
    'anio', 'mes', 'dia', 'trimestre',
    'es_dia_semana', 'es_fin_de_semana', 'es_fin_mes', 
    'es_festivo', 'es_dia_laboral', 'mes_sin', 'mes_cos',
    
    # Demográficas (grupo etario encodeado)
    'edad_persona',  # 0=ADOLESCENTES, 1=ADULTOS, 2=MENORES
    
    # Geoespaciales
    'codigo_municipio', 'area_km2', 'densidad_poblacional',
    'poblacion_total', 'n_centros_poblados', 'centros_por_km2',
    
    # Proporciones demográficas del municipio
    'proporcion_menores', 'proporcion_adultos', 'proporcion_adolescentes',
    
    # Histórico de delitos (one-hot)
    'ABIGEATO', 'AMENAZAS', 'DELITOS SEXUALES', 'EXTORSION',
    'HOMICIDIOS', 'HURTOS', 'LESIONES', 'VIOLENCIA INTRAFAMILIAR'
]
```

### Uso en el Tablero Web

```python
import joblib
import pandas as pd
import numpy as np

# Cargar modelo y artefactos
MODEL_DIR = 'models/predictivos/classification_event/'
modelo = joblib.load(MODEL_DIR + 'xgb_multioutput_event.joblib')
le_delito = joblib.load(MODEL_DIR + 'label_encoder_delito.joblib')
le_perfil = joblib.load(MODEL_DIR + 'label_encoder_perfil.joblib')
le_edad = joblib.load(MODEL_DIR + 'label_encoder_edad.joblib')
scaler = joblib.load(MODEL_DIR + 'scaler.joblib')

def predecir_evento(datos_usuario):
    """
    Predice delito y perfil basado en filtros del usuario.
    
    Args:
        datos_usuario: dict con valores de los filtros del tablero
    
    Returns:
        dict con predicción de delito y perfil
    """
    # Encodear grupo etario
    grupo_etario = datos_usuario.get('grupo_etario', 'ADULTOS')
    edad_encoded = le_edad.transform([grupo_etario])[0]
    
    # Preparar features
    evento = {
        'anio': datos_usuario.get('anio', 2025),
        'mes': datos_usuario.get('mes', 1),
        'dia': datos_usuario.get('dia', 15),
        'trimestre': (datos_usuario.get('mes', 1) - 1) // 3 + 1,
        'es_dia_semana': datos_usuario.get('es_dia_semana', 1),
        'es_fin_de_semana': datos_usuario.get('es_fin_de_semana', 0),
        'es_fin_mes': 1 if datos_usuario.get('dia', 15) >= 28 else 0,
        'es_festivo': datos_usuario.get('es_festivo', 0),
        'es_dia_laboral': 1 - datos_usuario.get('es_fin_de_semana', 0),
        'mes_sin': np.sin(2 * np.pi * datos_usuario.get('mes', 1) / 12),
        'mes_cos': np.cos(2 * np.pi * datos_usuario.get('mes', 1) / 12),
        'edad_persona': edad_encoded,
        'codigo_municipio': datos_usuario.get('codigo_municipio', 68001),
        # ... resto de features del municipio
    }
    
    # Crear DataFrame y escalar
    X = pd.DataFrame([evento])
    X_scaled = scaler.transform(X)
    
    # Predecir
    prediccion = modelo.predict(X_scaled)
    
    # Decodificar
    delito = le_delito.inverse_transform([prediccion[0][0]])[0]
    perfil = le_perfil.inverse_transform([prediccion[0][1]])[0]
    
    # Obtener probabilidades
    proba_delito = modelo.estimators_[0].predict_proba(X_scaled)[0]
    proba_perfil = modelo.estimators_[1].predict_proba(X_scaled)[0]
    
    return {
        'delito_predicho': delito,
        'perfil_predicho': perfil,
        'probabilidades_delito': dict(zip(le_delito.classes_, proba_delito.tolist())),
        'probabilidades_perfil': dict(zip(le_perfil.classes_, proba_perfil.tolist()))
    }

# Ejemplo de uso en el tablero
resultado = predecir_evento({
    'anio': 2025,
    'mes': 12,
    'grupo_etario': 'ADULTOS',
    'codigo_municipio': 68001,  # Bucaramanga
    'es_fin_de_semana': 0
})

print(f"Delito probable: {resultado['delito_predicho']}")
print(f"Perfil probable: {resultado['perfil_predicho']}")
```

### Uso en el Chatbot

```python
def responder_prediccion(pregunta, contexto):
    """
    Responde preguntas predictivas del chatbot.
    
    Ejemplos:
    - "¿Qué delito es más probable en Bucaramanga en diciembre?"
    - "¿Qué pasa si es un adulto en fin de semana?"
    """
    # Extraer contexto de la pregunta
    datos = extraer_contexto(pregunta)  # Función que parsea la pregunta
    
    # Hacer predicción
    resultado = predecir_evento(datos)
    
    # Generar respuesta natural
    respuesta = f"""
    Basándome en el contexto proporcionado:
    
    📊 **Predicción:**
    - Delito más probable: {resultado['delito_predicho']}
    - Perfil asociado: {resultado['perfil_predicho']}
    
    📈 **Probabilidades de delito:**
    """
    
    # Ordenar por probabilidad
    probs = sorted(
        resultado['probabilidades_delito'].items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    for delito, prob in probs[:3]:
        respuesta += f"\n    - {delito}: {prob*100:.1f}%"
    
    return respuesta

# Ejemplo
print(responder_prediccion(
    "¿Qué delito es más probable para un adulto en Bucaramanga en diciembre?",
    contexto={'municipio': 'Bucaramanga', 'mes': 12, 'grupo_etario': 'ADULTOS'}
))
```

### Preguntas que Responde

| Pregunta | Tipo de Respuesta |
|----------|-------------------|
| ¿Qué delito es más probable en [municipio] en [mes]? | Predicción + probabilidades |
| ¿Qué perfil está asociado a [contexto]? | Predicción de perfil |
| ¿Cuál es el riesgo para [grupo etario] en [zona]? | Análisis de riesgo |
| ¿Qué factores influyen más en [delito]? | Feature importance |

---

## 3. Comparación: Descriptivo vs Predictivo

| Aspecto | Descriptivo | Predictivo |
|---------|-------------|------------|
| **Finalidad** | Mostrar datos históricos | Predecir eventos futuros |
| **Velocidad** | Instantánea (pre-calculado) | Requiere inferencia |
| **Preguntas** | "¿Cuántos?", "¿Cuál fue?" | "¿Qué pasará?", "¿Qué es probable?" |
| **Actualización** | Re-ejecutar notebook | Re-entrenar modelo |
| **Complejidad** | Baja | Alta |
| **Uso principal** | Dashboard, KPIs | Alertas, predicciones |

---

## 4. Integración Completa

### Flujo del Chatbot

```python
def procesar_pregunta(pregunta):
    """
    Determina si la pregunta es descriptiva o predictiva
    y usa el modelo apropiado.
    """
    # Palabras clave predictivas
    palabras_predictivas = ['probable', 'predecir', 'pasará', 'riesgo', 'futuro']
    
    es_predictiva = any(p in pregunta.lower() for p in palabras_predictivas)
    
    if es_predictiva:
        # Usar modelo predictivo
        return responder_prediccion(pregunta)
    else:
        # Usar datos descriptivos
        return responder_pregunta(pregunta)
```

### Flujo del Tablero

```
┌─────────────────────────────────────────────────────────────┐
│                    TABLERO WEB                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐     ┌─────────────────┐               │
│  │   KPIs Header   │     │   Filtros       │               │
│  │  (Descriptivo)  │     │   Usuario       │               │
│  └─────────────────┘     └────────┬────────┘               │
│                                   │                         │
│  ┌─────────────────┐              ▼                         │
│  │   Gráficos      │     ┌─────────────────┐               │
│  │  Históricos     │     │   Predicción    │               │
│  │  (Descriptivo)  │     │   en Vivo       │               │
│  └─────────────────┘     │  (Predictivo)   │               │
│                          └─────────────────┘               │
│  ┌─────────────────┐                                       │
│  │   Mapa de       │     ┌─────────────────┐               │
│  │   Calor         │     │   Alertas       │               │
│  │  (Descriptivo)  │     │  (Predictivo)   │               │
│  └─────────────────┘     └─────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Notas Técnicas

### Grupos Etarios

El dataset NO contiene edades numéricas, sino categorías:

| Categoría | Código |
|-----------|--------|
| ADOLESCENTES | 0 |
| ADULTOS | 1 |
| MENORES | 2 |

### Perfiles

Clasificación de la persona en el evento:

- Víctima de cada tipo de delito
- Agresor de cada tipo de delito

### Actualización de Modelos

1. **Descriptivo**: Re-ejecutar `05_classification_event_descript.ipynb`
2. **Predictivo**: Re-ejecutar `05_eda_classification_event.ipynb`

---

## 6. Métricas del Modelo Predictivo

Consultar `models/predictivos/classification_event/metadata.json` para:

- Accuracy por target
- F1-Score por target
- Hiperparámetros optimizados
- Período de datos de entrenamiento
