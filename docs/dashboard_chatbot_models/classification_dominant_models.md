# Modelos de Clasificación Dominante: Guía de Uso

Este documento explica los dos modelos generados para el análisis de delitos/armas dominantes por municipio en Santander.

---

## 📊 Comparativa General

| Aspecto | Modelo Descriptivo | Modelo Predictivo |
|---------|-------------------|-------------------|
| **Pregunta que responde** | ¿Qué pasó? ¿Qué está pasando? | ¿Qué pasará? |
| **Tipo de análisis** | Estadísticas agregadas, tendencias | Machine Learning (XGBoost) |
| **Output** | Archivos JSON | Modelo `.joblib` + predicciones |
| **Para el chatbot** | ⭐ Muy útil | Útil para alertas |
| **Para el tablero** | ⭐ Muy útil | Útil para predicciones |
| **Complejidad** | Simple | Más complejo |

---

## 🔵 MODELO DESCRIPTIVO

### Ubicación
```
models/descriptivo/classification_dominant/
├── estadisticas_generales.json
├── tendencias_anuales.json
├── municipios_resumen.json
└── metadata.json
```

### ¿Qué contiene cada archivo?

#### 1. `estadisticas_generales.json`
Métricas globales del departamento de Santander.

```json
{
  "periodo": {"inicio": 2010, "fin": 2024},
  "total_municipios": 87,
  "suma_delitos_dominantes": 150000,
  "delito_mas_frecuente": {
    "nombre": "HURTO A PERSONAS",
    "porcentaje": 35.2
  },
  "arma_mas_frecuente": {
    "nombre": "SIN EMPLEO DE ARMAS",
    "porcentaje": 45.8
  },
  "distribucion_delitos": {...},
  "distribucion_armas": {...}
}
```

#### 2. `tendencias_anuales.json`
Evolución temporal y estacionalidad.

```json
{
  "delitos_por_anio": {"2010": 8500, "2011": 9200, ...},
  "cambio_porcentual": {"2011": 8.2, "2012": -3.5, ...},
  "tendencia_general": "creciente",
  "estacionalidad_mensual": {"Ene": 125.3, "Feb": 118.7, ...},
  "mes_mas_critico": "Dic",
  "mes_mas_tranquilo": "Feb",
  "delito_dominante_por_anio": {"2010": "HURTO A PERSONAS", ...}
}
```

#### 3. `municipios_resumen.json`
Resumen detallado por cada municipio (clave = código DANE).

```json
{
  "68001": {
    "codigo_municipio": 68001,
    "ranking_departamental": 1,
    "categoria_riesgo": "Alto",
    "total_delitos": 45000,
    "promedio_mensual": 250.5,
    "delito_mas_frecuente": "HURTO A PERSONAS",
    "arma_mas_frecuente": "SIN EMPLEO DE ARMAS",
    "mes_mas_critico": "Dic",
    "tendencia": {
      "cambio_vs_anio_anterior": 5.2,
      "direccion": "aumentando"
    },
    "comparativa": {
      "vs_promedio_depto": 150.3,
      "descripcion": "por encima"
    },
    "descripcion_chatbot": "El municipio con código 68001 ocupa el puesto #1..."
  }
}
```

---

### 🤖 Uso en el Chatbot

El modelo descriptivo es **ideal** para el chatbot porque permite responder preguntas en lenguaje natural.

#### Preguntas que puede responder:

| Pregunta del usuario | Datos a usar | Campo JSON |
|---------------------|--------------|------------|
| "¿Cuál es el delito más común en Santander?" | `estadisticas_generales.json` | `delito_mas_frecuente.nombre` |
| "¿Cuál es el delito más común en mi municipio?" | `municipios_resumen.json` | `[codigo].delito_mas_frecuente` |
| "¿Ha aumentado la criminalidad?" | `municipios_resumen.json` | `[codigo].tendencia.direccion` |
| "¿Qué tan seguro es este municipio?" | `municipios_resumen.json` | `[codigo].categoria_riesgo` |
| "¿Cuál es el mes más peligroso?" | `municipios_resumen.json` | `[codigo].mes_mas_critico` |
| "¿Cómo se compara con otros municipios?" | `municipios_resumen.json` | `[codigo].comparativa` |
| "Dame información general" | `municipios_resumen.json` | `[codigo].descripcion_chatbot` |

#### Ejemplo de implementación en Python:

```python
import json

# Cargar datos
with open('models/descriptivo/classification_dominant/municipios_resumen.json') as f:
    municipios = json.load(f)

with open('models/descriptivo/classification_dominant/estadisticas_generales.json') as f:
    stats = json.load(f)

def responder_chatbot(pregunta: str, codigo_municipio: int = None) -> str:
    pregunta = pregunta.lower()
    
    # Pregunta sobre municipio específico
    if codigo_municipio and str(codigo_municipio) in municipios:
        mun = municipios[str(codigo_municipio)]
        
        if 'delito' in pregunta and 'común' in pregunta:
            return f"El delito más común es {mun['delito_mas_frecuente']}."
        
        elif 'seguro' in pregunta or 'riesgo' in pregunta:
            return f"Tiene un nivel de riesgo {mun['categoria_riesgo']} (puesto #{mun['ranking_departamental']})."
        
        elif 'aumentado' in pregunta or 'tendencia' in pregunta:
            return f"La criminalidad está {mun['tendencia']['direccion']} ({mun['tendencia']['cambio_vs_anio_anterior']:+.1f}%)."
        
        else:
            return mun['descripcion_chatbot']
    
    # Preguntas generales
    elif 'santander' in pregunta and 'delito' in pregunta:
        return f"El delito más común en Santander es {stats['delito_mas_frecuente']['nombre']}."
    
    return "No tengo información suficiente."
```

---

### 📈 Uso en el Tablero Web

#### Visualizaciones recomendadas:

| Visualización | Archivo JSON | Campos |
|--------------|--------------|--------|
| **Mapa de calor por riesgo** | `municipios_resumen.json` | `categoria_riesgo` |
| **Ranking de municipios** | `municipios_resumen.json` | `ranking_departamental`, `total_delitos` |
| **Gráfico de tendencia anual** | `tendencias_anuales.json` | `delitos_por_anio` |
| **Gráfico de estacionalidad** | `tendencias_anuales.json` | `estacionalidad_mensual` |
| **Pie chart de delitos** | `estadisticas_generales.json` | `distribucion_delitos` |
| **Indicadores KPI** | `estadisticas_generales.json` | Varios |

#### Ejemplo para mapa en JavaScript/React:

```javascript
// Colorear municipios por nivel de riesgo
const coloresRiesgo = {
  'Bajo': '#22c55e',      // Verde
  'Medio-Bajo': '#eab308', // Amarillo
  'Medio-Alto': '#f97316', // Naranja
  'Alto': '#ef4444'        // Rojo
};

function getColorMunicipio(codigoMunicipio) {
  const mun = municipiosResumen[codigoMunicipio];
  return coloresRiesgo[mun.categoria_riesgo];
}
```

---

## 🔴 MODELO PREDICTIVO

### Ubicación
```
models/classification_dominant/
├── xgb_multioutput.joblib        # Modelo entrenado
├── label_encoder_delito.joblib   # Encoder para delitos
├── label_encoder_arma.joblib     # Encoder para armas
├── scaler.joblib                 # Escalador de features
└── metadata.json                 # Información del modelo
```

### ¿Qué predice?

Es un modelo **Multi-Output** que predice simultáneamente:
1. **delito_dominante**: Qué tipo de delito será más frecuente el próximo mes
2. **arma_dominante**: Qué tipo de arma será más usada el próximo mes

### Features que utiliza (15 columnas):

| Feature | Descripción |
|---------|-------------|
| `anio` | Año de la predicción |
| `mes` | Mes de la predicción |
| `codigo_municipio` | Código DANE del municipio |
| `count_delito` | Conteo actual de delitos |
| `count_arma` | Conteo actual de armas |
| `mes_sin`, `mes_cos` | Codificación cíclica del mes |
| `count_delito_lag1/2/3` | Delitos de los 3 meses anteriores |
| `count_arma_lag1/2/3` | Armas de los 3 meses anteriores |
| `count_delito_ma3` | Media móvil 3 meses (delitos) |
| `count_arma_ma3` | Media móvil 3 meses (armas) |

---

### 🤖 Uso en el Chatbot

El modelo predictivo es útil para el chatbot cuando el usuario pregunta sobre el **futuro**.

#### Preguntas que puede responder:

| Pregunta del usuario | Cómo responder |
|---------------------|----------------|
| "¿Qué delito habrá más el próximo mes?" | Ejecutar predicción |
| "¿Qué puedo esperar en diciembre?" | Ejecutar predicción para mes=12 |
| "¿Debería preocuparme el próximo mes?" | Comparar predicción con promedio histórico |

#### Ejemplo de implementación:

```python
import joblib
import numpy as np
import pandas as pd

# Cargar modelo y transformadores
model = joblib.load('models/classification_dominant/xgb_multioutput.joblib')
le_delito = joblib.load('models/classification_dominant/label_encoder_delito.joblib')
le_arma = joblib.load('models/classification_dominant/label_encoder_arma.joblib')
scaler = joblib.load('models/classification_dominant/scaler.joblib')

def predecir_proximo_mes(codigo_municipio: int, datos_historicos: pd.DataFrame) -> dict:
    """
    Predice el delito y arma dominante para el próximo mes.
    
    Args:
        codigo_municipio: Código DANE del municipio
        datos_historicos: DataFrame con los últimos 3 meses del municipio
    """
    # Preparar features (ejemplo simplificado)
    ultimo_registro = datos_historicos.iloc[-1]
    
    # Calcular mes siguiente
    proximo_mes = (ultimo_registro['mes'] % 12) + 1
    proximo_anio = ultimo_registro['anio'] + (1 if proximo_mes == 1 else 0)
    
    # Construir features
    features = {
        'anio': proximo_anio,
        'mes': proximo_mes,
        'codigo_municipio': codigo_municipio,
        'count_delito': ultimo_registro['count_delito'],
        'count_arma': ultimo_registro['count_arma'],
        'mes_sin': np.sin(2 * np.pi * proximo_mes / 12),
        'mes_cos': np.cos(2 * np.pi * proximo_mes / 12),
        'count_delito_lag1': datos_historicos.iloc[-1]['count_delito'],
        'count_delito_lag2': datos_historicos.iloc[-2]['count_delito'],
        'count_delito_lag3': datos_historicos.iloc[-3]['count_delito'],
        'count_arma_lag1': datos_historicos.iloc[-1]['count_arma'],
        'count_arma_lag2': datos_historicos.iloc[-2]['count_arma'],
        'count_arma_lag3': datos_historicos.iloc[-3]['count_arma'],
        'count_delito_ma3': datos_historicos['count_delito'].tail(3).mean(),
        'count_arma_ma3': datos_historicos['count_arma'].tail(3).mean(),
    }
    
    # Escalar y predecir
    X = pd.DataFrame([features])
    X_scaled = scaler.transform(X)
    predicciones = model.predict(X_scaled)
    
    # Decodificar predicciones
    delito_pred = le_delito.inverse_transform([predicciones[0][0]])[0]
    arma_pred = le_arma.inverse_transform([predicciones[0][1]])[0]
    
    return {
        'mes_prediccion': proximo_mes,
        'anio_prediccion': proximo_anio,
        'delito_predicho': delito_pred,
        'arma_predicha': arma_pred
    }

# Uso en chatbot
def responder_prediccion(codigo_municipio, datos_historicos):
    pred = predecir_proximo_mes(codigo_municipio, datos_historicos)
    return f"Para {pred['mes_prediccion']}/{pred['anio_prediccion']}, se espera que el delito más frecuente sea {pred['delito_predicho']}, principalmente con {pred['arma_predicha']}."
```

---

### 📈 Uso en el Tablero Web

#### Visualizaciones recomendadas:

| Visualización | Descripción |
|--------------|-------------|
| **Mapa predictivo** | Colorear municipios según delito predicho para el próximo mes |
| **Timeline de predicciones** | Mostrar predicciones para los próximos 3-6 meses |
| **Comparativa real vs predicho** | Evaluar precisión del modelo |
| **Alertas por municipio** | Destacar donde se espera aumento de criminalidad |

#### Ejemplo de alerta:

```javascript
// Generar alertas cuando la predicción indica cambio de patrón
function generarAlerta(municipio, prediccion, historico) {
  const delitoActual = historico.delito_dominante;
  const delitoPredicho = prediccion.delito_predicho;
  
  if (delitoActual !== delitoPredicho) {
    return {
      tipo: 'cambio_patron',
      mensaje: `Se espera cambio de ${delitoActual} a ${delitoPredicho}`,
      municipio: municipio,
      severidad: 'media'
    };
  }
  return null;
}
```

---

## 🎯 Recomendación de Uso Combinado

Para el **Tablero Web Inteligente de Seguridad Ciudadana**, se recomienda usar **ambos modelos**:

### Vista Principal del Tablero

```
┌─────────────────────────────────────────────────────────────┐
│  📊 TABLERO DE SEGURIDAD CIUDADANA - SANTANDER              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ ANÁLISIS ACTUAL     │  │ PREDICCIÓN          │          │
│  │ (Modelo Descriptivo)│  │ (Modelo Predictivo) │          │
│  │                     │  │                     │          │
│  │ • Delito más común  │  │ • Próximo mes:      │          │
│  │ • Tendencia actual  │  │   Hurto a personas  │          │
│  │ • Ranking municipio │  │ • Alerta: ⚠️        │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              MAPA DE SANTANDER                       │   │
│  │   🟢 Bajo  🟡 Medio-Bajo  🟠 Medio-Alto  🔴 Alto    │   │
│  │                                                      │   │
│  │   Toggle: [Riesgo Actual] [Predicción Próximo Mes]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Para el Chatbot

```
Usuario: "¿Cómo está la seguridad en Bucaramanga?"

Chatbot (usando DESCRIPTIVO):
"Bucaramanga ocupa el puesto #1 en criminalidad del departamento 
con nivel de riesgo Alto. El delito más frecuente es Hurto a 
Personas. Respecto al año anterior, la criminalidad está estable."

Usuario: "¿Y qué pasará el próximo mes?"

Chatbot (usando PREDICTIVO):
"Para el próximo mes, se espera que el delito más frecuente 
siga siendo Hurto a Personas, principalmente sin empleo de armas."
```

---

## 📁 Resumen de Archivos

| Modelo | Archivo | Propósito |
|--------|---------|-----------|
| **Descriptivo** | `estadisticas_generales.json` | KPIs globales |
| **Descriptivo** | `tendencias_anuales.json` | Gráficos de tendencia |
| **Descriptivo** | `municipios_resumen.json` | Respuestas del chatbot |
| **Predictivo** | `xgb_multioutput.joblib` | Hacer predicciones |
| **Predictivo** | `label_encoder_*.joblib` | Decodificar predicciones |
| **Predictivo** | `scaler.joblib` | Preprocesar nuevos datos |

---

## ⚠️ Limitaciones

### Modelo Descriptivo
- Solo describe datos históricos, no predice
- Requiere actualización periódica cuando hay nuevos datos

### Modelo Predictivo
- Precisión limitada por calidad de datos históricos
- No incluye horarios ni cuadrantes (datos no disponibles)
- Requiere datos de los últimos 3 meses para generar features lag
