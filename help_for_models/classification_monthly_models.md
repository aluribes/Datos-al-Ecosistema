# Modelos de Clasificación Mensual de Riesgo: Guía de Uso

Este documento explica los dos modelos generados para el análisis y predicción del nivel de riesgo mensual por municipio en Santander.

---

## 📊 Comparativa General

| Aspecto | Modelo Descriptivo | Modelo Predictivo |
|---------|-------------------|-------------------|
| **Pregunta que responde** | ¿Cómo se distribuye el riesgo? ¿Qué patrones hay? | ¿Cuál será el nivel de riesgo? ¿Habrá incremento? |
| **Tipo de análisis** | Estadísticas agregadas, distribuciones | Machine Learning (RandomForest) |
| **Output** | 5 archivos JSON | 2 modelos `.joblib` + transformadores |
| **Para el chatbot** | ⭐ Muy útil (respuestas instantáneas) | Útil para predicciones |
| **Para el tablero** | ⭐ Muy útil (KPIs, gráficos) | Útil para alertas predictivas |
| **Complejidad** | Simple (lectura de JSON) | Más complejo (inferencia ML) |

---

## 🔵 MODELO DESCRIPTIVO

### Ubicación
```
models/descriptivo/classification_monthly/
├── estadisticas_generales.json     # Métricas globales
├── riesgo_por_municipio.json       # Análisis por municipio
├── tendencias_temporales.json      # Patrones temporales
├── analisis_delitos.json           # Estadísticas por tipo de delito
└── respuestas_chatbot.json         # Respuestas pre-generadas
```

### ¿Qué contiene cada archivo?

#### 1. `estadisticas_generales.json`
Métricas globales del dataset y distribución de riesgo.

```json
{
  "fecha_generacion": "2025-01-15 10:30:00",
  "dataset": "classification_monthly_dataset.parquet",
  "periodo": {
    "inicio": 2010,
    "fin": 2024,
    "total_meses": 180
  },
  "cobertura": {
    "total_registros": 15000,
    "municipios": 87,
    "registros_por_municipio": 172.4
  },
  "distribucion_riesgo": {
    "BAJO": {"cantidad": 8000, "porcentaje": 53.33},
    "MEDIO": {"cantidad": 4500, "porcentaje": 30.00},
    "ALTO": {"cantidad": 2500, "porcentaje": 16.67}
  },
  "delitos": {
    "total_acumulado": 250000,
    "promedio_mensual": 16.67,
    "maximo_mensual": 450,
    "municipio_max_delitos": 68001
  }
}
```

#### 2. `riesgo_por_municipio.json`
Estadísticas detalladas para cada municipio (clave = código DANE).

```json
{
  "68001": {
    "total_registros": 180,
    "nivel_predominante": "ALTO",
    "distribucion_riesgo": {
      "BAJO": 15.5,
      "MEDIO": 28.3,
      "ALTO": 56.2
    },
    "delitos": {
      "total": 45000,
      "promedio_mensual": 250.0,
      "maximo_mensual": 450
    },
    "tendencia": {
      "variacion_anual_pct": 5.2,
      "direccion": "incremento"
    },
    "poblacion_total": 580000,
    "densidad_poblacional": 2500.5
  }
}
```

#### 3. `tendencias_temporales.json`
Análisis de patrones por año y mes (estacionalidad).

```json
{
  "por_anio": {
    "2023": {
      "total_delitos": 18500,
      "promedio_mensual": 17.5,
      "distribucion_riesgo": {
        "BAJO": 48.5,
        "MEDIO": 32.1,
        "ALTO": 19.4
      }
    }
  },
  "por_mes": {
    "1": {
      "nombre": "Enero",
      "total_delitos": 1200,
      "promedio": 14.5,
      "pct_riesgo_alto": 18.2
    }
  },
  "estacionalidad": {
    "meses_mas_riesgo": [
      {"mes": 12, "nombre": "Diciembre", "pct_alto": 25.3}
    ],
    "meses_menos_riesgo": [
      {"mes": 2, "nombre": "Febrero", "pct_alto": 12.1}
    ]
  }
}
```

#### 4. `analisis_delitos.json`
Estadísticas por cada tipo de delito.

```json
{
  "HURTOS": {
    "total_historico": 85000,
    "promedio_mensual": 5.67,
    "porcentaje_del_total": 34.0,
    "municipio_mas_casos": 68001,
    "tendencia_anual_pct": 3.2
  },
  "HOMICIDIOS": {
    "total_historico": 2500,
    "promedio_mensual": 0.17,
    "porcentaje_del_total": 1.0,
    "municipio_mas_casos": 68001,
    "tendencia_anual_pct": -5.8
  }
}
```

#### 5. `respuestas_chatbot.json`
Respuestas pre-calculadas para consultas frecuentes.

```json
{
  "municipios_mas_seguros": [
    {"codigo": 68318, "pct_bajo": 78.5, "promedio_delitos": 2.3}
  ],
  "municipios_menos_seguros": [
    {"codigo": 68001, "pct_alto": 56.2, "promedio_delitos": 250.0}
  ],
  "meses_mas_peligrosos": [
    {"mes": 12, "nombre": "Diciembre", "pct_alto": 25.3}
  ],
  "meses_mas_seguros": [
    {"mes": 2, "nombre": "Febrero", "pct_alto": 12.1}
  ],
  "delito_mas_frecuente": {
    "tipo": "HURTOS",
    "total": 85000,
    "porcentaje": 34.0
  },
  "resumen_general": {
    "total_delitos": 250000,
    "promedio_mensual_departamento": 16.67,
    "municipios_analizados": 87,
    "periodo": "2010-2024"
  },
  "preguntas_frecuentes": {
    "¿Cuál es el municipio más seguro?": "El municipio con código 68318 tiene 78.5% de meses en riesgo BAJO.",
    "¿Cuál es el mes más peligroso?": "Diciembre tiene 25.3% de riesgo alto.",
    "¿Qué delito es más común?": "HURTOS representa el 34.0% del total de delitos.",
    "¿Cuántos delitos hay en promedio?": "En promedio hay 16.7 delitos por municipio al mes."
  }
}
```

---

### 🤖 Uso en el Chatbot

El modelo descriptivo es **ideal** para el chatbot porque permite responder preguntas instantáneamente sin necesidad de ejecutar modelos ML.

#### Preguntas que puede responder:

| Pregunta del usuario | Archivo JSON | Campo a usar |
|---------------------|--------------|--------------|
| "¿Cuál es el municipio más seguro?" | `respuestas_chatbot.json` | `municipios_mas_seguros[0]` |
| "¿Cuál es el municipio más peligroso?" | `respuestas_chatbot.json` | `municipios_menos_seguros[0]` |
| "¿Qué mes tiene más riesgo?" | `respuestas_chatbot.json` | `meses_mas_peligrosos[0]` |
| "¿Cuál es el delito más común?" | `respuestas_chatbot.json` | `delito_mas_frecuente` |
| "¿Cómo está el riesgo en [municipio]?" | `riesgo_por_municipio.json` | `[codigo].nivel_predominante` |
| "¿Ha aumentado el crimen en [municipio]?" | `riesgo_por_municipio.json` | `[codigo].tendencia.direccion` |
| "¿Cómo evolucionó el riesgo en 2023?" | `tendencias_temporales.json` | `por_anio.2023` |
| "¿Cuántos delitos hay en total?" | `estadisticas_generales.json` | `delitos.total_acumulado` |

#### Ejemplo de implementación en Python:

```python
import json
from pathlib import Path

# Cargar datos pre-calculados
MODEL_PATH = Path('models/descriptivo/classification_monthly/')

with open(MODEL_PATH / 'respuestas_chatbot.json', 'r', encoding='utf-8') as f:
    respuestas = json.load(f)

with open(MODEL_PATH / 'riesgo_por_municipio.json', 'r', encoding='utf-8') as f:
    municipios = json.load(f)

with open(MODEL_PATH / 'tendencias_temporales.json', 'r', encoding='utf-8') as f:
    tendencias = json.load(f)

def responder_pregunta(pregunta: str, codigo_municipio: int = None) -> str:
    """
    Responde preguntas sobre riesgo mensual usando datos pre-calculados.
    """
    pregunta = pregunta.lower()
    
    # Preguntas sobre municipio específico
    if codigo_municipio and str(codigo_municipio) in municipios:
        mun = municipios[str(codigo_municipio)]
        
        if 'riesgo' in pregunta or 'seguro' in pregunta or 'peligro' in pregunta:
            nivel = mun['nivel_predominante']
            pct = mun['distribucion_riesgo'][nivel]
            return f"El nivel de riesgo predominante es {nivel} ({pct:.1f}% de los meses)."
        
        elif 'aumentado' in pregunta or 'tendencia' in pregunta:
            tendencia = mun['tendencia']['direccion']
            cambio = mun['tendencia']['variacion_anual_pct']
            return f"La criminalidad muestra {tendencia} ({cambio:+.1f}% vs año anterior)."
        
        elif 'delitos' in pregunta or 'promedio' in pregunta:
            return f"Hay un promedio de {mun['delitos']['promedio_mensual']:.1f} delitos mensuales."
    
    # Preguntas generales
    if 'más seguro' in pregunta:
        mun = respuestas['municipios_mas_seguros'][0]
        return f"El municipio más seguro es el {mun['codigo']} con {mun['pct_bajo']:.1f}% de riesgo bajo."
    
    elif 'más peligroso' in pregunta or 'menos seguro' in pregunta:
        mun = respuestas['municipios_menos_seguros'][0]
        return f"El municipio con más riesgo es el {mun['codigo']} con {mun['pct_alto']:.1f}% de riesgo alto."
    
    elif 'mes' in pregunta and ('peligro' in pregunta or 'riesgo' in pregunta):
        mes = respuestas['meses_mas_peligrosos'][0]
        return f"{mes['nombre']} es el mes más peligroso con {mes['pct_alto']:.1f}% de riesgo alto."
    
    elif 'delito' in pregunta and 'común' in pregunta:
        delito = respuestas['delito_mas_frecuente']
        return f"{delito['tipo']} es el delito más común ({delito['porcentaje']:.1f}% del total)."
    
    # Respuestas pre-definidas
    if pregunta in respuestas['preguntas_frecuentes']:
        return respuestas['preguntas_frecuentes'][pregunta]
    
    return "Lo siento, no tengo información específica sobre eso."

# Ejemplo de uso
print(responder_pregunta("¿Cuál es el municipio más seguro?"))
print(responder_pregunta("¿Cuál es el mes más peligroso?"))
print(responder_pregunta("¿Qué delito es más común?"))
print(responder_pregunta("¿Ha aumentado el crimen?", codigo_municipio=68001))
```

---

### 📈 Uso en el Tablero Web

#### Visualizaciones recomendadas:

| Visualización | Archivo JSON | Campos a usar |
|--------------|--------------|---------------|
| **Mapa de calor por riesgo** | `riesgo_por_municipio.json` | `[cod].nivel_predominante` |
| **KPIs principales** | `estadisticas_generales.json` | Varios |
| **Ranking municipios** | `respuestas_chatbot.json` | `municipios_mas_seguros`, `municipios_menos_seguros` |
| **Gráfico de tendencia anual** | `tendencias_temporales.json` | `por_anio` |
| **Gráfico de estacionalidad** | `tendencias_temporales.json` | `por_mes` |
| **Distribución de riesgo (pie)** | `estadisticas_generales.json` | `distribucion_riesgo` |
| **Barras por tipo de delito** | `analisis_delitos.json` | Todos |

#### Ejemplo para mapa en JavaScript/React:

```javascript
// Cargar datos
const riesgoPorMunicipio = await fetch('/api/riesgo_por_municipio.json').then(r => r.json());

// Colores por nivel de riesgo
const coloresRiesgo = {
  'BAJO': '#22c55e',   // Verde
  'MEDIO': '#eab308',  // Amarillo
  'ALTO': '#ef4444'    // Rojo
};

// Función para colorear municipio en el mapa
function getColorMunicipio(codigoMunicipio) {
  const mun = riesgoPorMunicipio[codigoMunicipio];
  return coloresRiesgo[mun.nivel_predominante];
}

// Función para tooltip
function getTooltipMunicipio(codigoMunicipio) {
  const mun = riesgoPorMunicipio[codigoMunicipio];
  return `
    <strong>Municipio ${codigoMunicipio}</strong><br/>
    Nivel de riesgo: ${mun.nivel_predominante}<br/>
    Promedio mensual: ${mun.delitos.promedio_mensual} delitos<br/>
    Tendencia: ${mun.tendencia.direccion} (${mun.tendencia.variacion_anual_pct}%)
  `;
}
```

#### Ejemplo de KPIs para dashboard:

```javascript
// Cargar estadísticas generales
const stats = await fetch('/api/estadisticas_generales.json').then(r => r.json());

// KPIs principales
const kpis = [
  {
    titulo: "Total Delitos",
    valor: stats.delitos.total_acumulado.toLocaleString(),
    icono: "📊"
  },
  {
    titulo: "Promedio Mensual",
    valor: stats.delitos.promedio_mensual.toFixed(1),
    icono: "📈"
  },
  {
    titulo: "Municipios Analizados",
    valor: stats.cobertura.municipios,
    icono: "🏘️"
  },
  {
    titulo: "% Riesgo Alto",
    valor: `${stats.distribucion_riesgo.ALTO.porcentaje}%`,
    icono: "⚠️",
    color: "#ef4444"
  }
];
```

---

## 🔴 MODELO PREDICTIVO

### Ubicación
```
models/predictivos/classification_monthly/
├── clasificador_riesgo.joblib         # Modelo nivel de riesgo
├── clasificador_incremento.joblib     # Modelo incremento de delitos
├── scaler.joblib                       # StandardScaler
├── label_encoder_riesgo.joblib         # LabelEncoder para nivel_riesgo
└── metadata.json                       # Información del modelo
```

### ¿Qué predice?

El modelo predictivo tiene **dos clasificadores RandomForest optimizados**:

| Modelo | Target | Tipo | Clases |
|--------|--------|------|--------|
| `clasificador_riesgo.joblib` | `nivel_riesgo` | Multiclase | BAJO, MEDIO, ALTO |
| `clasificador_incremento.joblib` | `incremento_delitos` | Binario | 0 (no), 1 (sí) |

### Features que utiliza:

Las features se definen dinámicamente pero típicamente incluyen:

| Categoría | Features | Descripción |
|-----------|----------|-------------|
| **Temporales** | `anio`, `mes`, `mes_sin`, `mes_cos` | Variables de tiempo |
| **Delitos base** | `HURTOS`, `HOMICIDIOS`, `LESIONES`, etc. | Conteo por tipo |
| **Agregados** | `total_delitos`, `promedio_delitos_3m` | Estadísticas agregadas |
| **Demográficas** | `poblacion_total`, `densidad_poblacional` | Datos poblacionales |
| **Lag features** | `total_delitos_lag1/2/3` | Valores históricos |

### Métricas del modelo:

```json
{
  "modelo_riesgo": {
    "accuracy": 0.85,
    "f1_macro": 0.82,
    "mejores_parametros": {
      "n_estimators": 200,
      "max_depth": 15,
      "min_samples_split": 5
    }
  },
  "modelo_incremento": {
    "accuracy": 0.88,
    "f1": 0.85,
    "mejores_parametros": {
      "n_estimators": 150,
      "max_depth": 10,
      "min_samples_split": 3
    }
  }
}
```

---

### 🤖 Uso en el Chatbot

El modelo predictivo es útil para responder preguntas sobre el **futuro**.

#### Preguntas que puede responder:

| Pregunta del usuario | Modelo a usar | Respuesta tipo |
|---------------------|---------------|----------------|
| "¿Qué nivel de riesgo habrá el próximo mes?" | `clasificador_riesgo` | "Se espera riesgo MEDIO" |
| "¿Aumentarán los delitos?" | `clasificador_incremento` | "Sí/No se espera incremento" |
| "¿Cómo estará [municipio] en diciembre?" | Ambos | Predicción combinada |

#### Ejemplo de implementación:

```python
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# Cargar modelos y transformadores
MODEL_PATH = Path('models/predictivos/classification_monthly/')

modelo_riesgo = joblib.load(MODEL_PATH / 'clasificador_riesgo.joblib')
modelo_incremento = joblib.load(MODEL_PATH / 'clasificador_incremento.joblib')
scaler = joblib.load(MODEL_PATH / 'scaler.joblib')
le_riesgo = joblib.load(MODEL_PATH / 'label_encoder_riesgo.joblib')

# Cargar metadata para obtener las features
with open(MODEL_PATH / 'metadata.json', 'r') as f:
    metadata = json.load(f)
FEATURE_COLS = metadata['feature_columns']

def predecir_riesgo_mensual(features_dict: dict) -> dict:
    """
    Predice el nivel de riesgo e incremento para el próximo mes.
    
    Args:
        features_dict: Diccionario con todas las features necesarias
        
    Returns:
        dict con predicciones de riesgo e incremento
    """
    # Crear DataFrame con features
    X = pd.DataFrame([features_dict])[FEATURE_COLS]
    
    # Escalar
    X_scaled = scaler.transform(X)
    
    # Predecir
    pred_riesgo_encoded = modelo_riesgo.predict(X_scaled)[0]
    pred_incremento = modelo_incremento.predict(X_scaled)[0]
    
    # Probabilidades
    prob_riesgo = modelo_riesgo.predict_proba(X_scaled)[0]
    prob_incremento = modelo_incremento.predict_proba(X_scaled)[0]
    
    # Decodificar riesgo
    nivel_riesgo = le_riesgo.inverse_transform([pred_riesgo_encoded])[0]
    
    return {
        'nivel_riesgo': nivel_riesgo,
        'confianza_riesgo': float(max(prob_riesgo)),
        'probabilidades_riesgo': {
            clase: float(prob) 
            for clase, prob in zip(le_riesgo.classes_, prob_riesgo)
        },
        'incremento_esperado': bool(pred_incremento),
        'probabilidad_incremento': float(prob_incremento[1]),
        'alerta': nivel_riesgo == 'ALTO' or pred_incremento == 1
    }

def responder_prediccion_chatbot(codigo_municipio: int, mes: int, anio: int, 
                                  datos_historicos: pd.DataFrame) -> str:
    """
    Genera respuesta para el chatbot basada en predicción.
    """
    # Construir features (ejemplo simplificado)
    ultimo = datos_historicos.iloc[-1]
    
    features = {
        'anio': anio,
        'mes': mes,
        'mes_sin': np.sin(2 * np.pi * mes / 12),
        'mes_cos': np.cos(2 * np.pi * mes / 12),
        'codigo_municipio': codigo_municipio,
        'total_delitos': ultimo['total_delitos'],
        'total_delitos_lag1': datos_historicos.iloc[-1]['total_delitos'],
        'total_delitos_lag2': datos_historicos.iloc[-2]['total_delitos'],
        'total_delitos_lag3': datos_historicos.iloc[-3]['total_delitos'],
        # ... otras features según FEATURE_COLS
    }
    
    # Predecir
    pred = predecir_riesgo_mensual(features)
    
    # Generar respuesta
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    respuesta = f"Para {meses[mes-1]} {anio} en el municipio {codigo_municipio}:\n"
    respuesta += f"- Nivel de riesgo esperado: {pred['nivel_riesgo']} (confianza: {pred['confianza_riesgo']:.1%})\n"
    
    if pred['incremento_esperado']:
        respuesta += f"- ⚠️ Se espera un incremento de delitos (probabilidad: {pred['probabilidad_incremento']:.1%})"
    else:
        respuesta += f"- ✅ No se espera incremento significativo de delitos"
    
    if pred['alerta']:
        respuesta += "\n\n🚨 ALERTA: Se recomienda tomar precauciones adicionales."
    
    return respuesta
```

---

### 📈 Uso en el Tablero Web

#### Visualizaciones recomendadas:

| Visualización | Modelo | Descripción |
|--------------|--------|-------------|
| **Mapa predictivo** | `clasificador_riesgo` | Colorear municipios por riesgo esperado |
| **Alertas de incremento** | `clasificador_incremento` | Lista de municipios con incremento esperado |
| **Probabilidades** | Ambos | Gauges con probabilidad de cada nivel |
| **Comparativa actual vs futuro** | Ambos | Antes/después por municipio |

#### Ejemplo de integración API:

```python
# FastAPI endpoint para predicciones
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PrediccionRequest(BaseModel):
    codigo_municipio: int
    mes: int
    anio: int
    features: dict

@app.post("/api/predecir-riesgo")
async def predecir_riesgo(request: PrediccionRequest):
    """
    Endpoint para obtener predicción de riesgo.
    """
    prediccion = predecir_riesgo_mensual(request.features)
    
    return {
        "municipio": request.codigo_municipio,
        "periodo": f"{request.mes}/{request.anio}",
        "prediccion": prediccion
    }
```

---

## 🔄 Flujo de Trabajo Recomendado

### Para el Chatbot:

```
Usuario pregunta
      │
      ▼
┌──────────────────────────────┐
│ ¿Es pregunta sobre el FUTURO? │
└──────────────────────────────┘
      │
    ┌─┴─┐
   NO   SÍ
    │    │
    ▼    ▼
┌───────┐ ┌──────────┐
│ JSON  │ │ Modelo   │
│ Desc. │ │ Predict. │
└───────┘ └──────────┘
    │         │
    ▼         ▼
Respuesta instantánea  Ejecutar inferencia
```

### Para el Tablero:

1. **Carga inicial**: Cargar todos los JSON del modelo descriptivo
2. **Vista actual**: Usar `riesgo_por_municipio.json` para el mapa y estadísticas
3. **Vista predictiva**: Usar modelos `.joblib` para generar predicciones bajo demanda
4. **Alertas**: Combinar ambos para identificar cambios significativos

---

## 📝 Notas Importantes

### Ventajas del Modelo Descriptivo:
- ✅ Respuestas instantáneas (sin procesamiento ML)
- ✅ Fácil de cachear y servir
- ✅ No requiere dependencias ML en producción
- ✅ Ideal para preguntas sobre el pasado y presente

### Ventajas del Modelo Predictivo:
- ✅ Puede responder sobre el futuro
- ✅ Se adapta a nuevos datos
- ✅ Proporciona probabilidades
- ✅ Útil para sistemas de alerta temprana

### Mantenimiento:
- **Descriptivo**: Re-generar mensualmente con datos actualizados
- **Predictivo**: Re-entrenar trimestralmente o cuando el rendimiento baje

### Limitaciones:
- Los modelos están entrenados con datos de Santander únicamente
- Las predicciones son más confiables a corto plazo (1-3 meses)
- Eventos extraordinarios (pandemia, cambios políticos) pueden afectar la precisión

---

## 📁 Resumen de Archivos

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `estadisticas_generales.json` | `descriptivo/` | Métricas globales |
| `riesgo_por_municipio.json` | `descriptivo/` | Análisis por municipio |
| `tendencias_temporales.json` | `descriptivo/` | Patrones temporales |
| `analisis_delitos.json` | `descriptivo/` | Stats por tipo de delito |
| `respuestas_chatbot.json` | `descriptivo/` | Respuestas pre-generadas |
| `clasificador_riesgo.joblib` | `predictivos/` | Modelo multiclase de riesgo |
| `clasificador_incremento.joblib` | `predictivos/` | Modelo binario de incremento |
| `scaler.joblib` | `predictivos/` | StandardScaler entrenado |
| `label_encoder_riesgo.joblib` | `predictivos/` | Encoder para niveles |
| `metadata.json` | `predictivos/` | Configuración y features |
