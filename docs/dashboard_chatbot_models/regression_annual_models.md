# Guía de Uso: Modelos de Regresión Anual de Delitos

## Descripción General

Este documento describe cómo integrar los modelos de regresión anual de delitos en **tableros de visualización (dashboards)** y **chatbots** para análisis de seguridad en Santander.

Se utilizan dos modelos complementarios:
- **Modelo Descriptivo**: Estadísticas pre-calculadas para respuestas instantáneas
- **Modelo Predictivo**: Predicción de delitos anuales por municipio

---

## 📁 Archivos Generados

### Modelo Descriptivo (`models/descriptivo/annual/`)

| Archivo | Descripción |
|---------|-------------|
| `perfiles_municipios_{timestamp}.json` | Perfil completo por municipio |
| `perfiles_clusters_{timestamp}.json` | Características de cada cluster |
| `descriptive_metadata_{timestamp}.json` | Metadata del modelo descriptivo |
| `municipios_perfilados_{timestamp}.parquet` | Dataset enriquecido con perfiles |

### Modelo Predictivo (`models/predictivos/regression_annual/`)

| Archivo | Descripción |
|---------|-------------|
| `xgb_regressor.joblib` | Modelo XGBoost entrenado |
| `scaler.joblib` | Escalador para preprocesamiento |
| `feature_columns.json` | Lista de features del modelo |
| `metadata.json` | Métricas y configuración |

---

## 🖥️ Integración en Tableros (Dashboard)

### 1. Visualización de Clusters de Municipios

```python
import json
import pandas as pd

# Cargar perfiles de clusters
with open('models/descriptivo/annual/perfiles_clusters_{timestamp}.json', 'r') as f:
    clusters = json.load(f)

# Datos para mapa o gráfico de clusters
for cluster_id, info in clusters.items():
    print(f"Cluster: {info['nombre']}")
    print(f"  - Municipios: {info['num_municipios']}")
    print(f"  - Delitos promedio: {info['estadisticas']['delitos_promedio']:.0f}")
    print(f"  - Tendencia: {info['tendencias']}")
```

**Componentes sugeridos:**
- **Mapa coroplético**: Colorear municipios por cluster
- **Gráfico radar**: Comparar perfiles de clusters
- **Tabla ranking**: Top municipios por nivel de riesgo

### 2. Panel de Tendencias Temporales

```python
# Usar perfiles de municipios para mostrar tendencias
with open('models/descriptivo/annual/perfiles_municipios_{timestamp}.json', 'r') as f:
    municipios = json.load(f)

# Contar tendencias
tendencias = {'Ascendente': 0, 'Descendente': 0, 'Estable': 0, 'Volatil': 0}
for cod, perfil in municipios.items():
    tendencia = perfil.get('tendencia', 'Sin datos')
    if tendencia in tendencias:
        tendencias[tendencia] += 1

# Gráfico de pie o barras
```

**Componentes sugeridos:**
- **Gráfico de pastel**: Distribución de tendencias
- **Indicadores KPI**: % municipios en alza vs baja
- **Timeline**: Evolución histórica por año

### 3. Predicciones Anuales

```python
import joblib
import pandas as pd
import json

# Cargar modelo predictivo
model = joblib.load('models/predictivos/regression_annual/xgb_regressor.joblib')
scaler = joblib.load('models/predictivos/regression_annual/scaler.joblib')

with open('models/predictivos/regression_annual/feature_columns.json', 'r') as f:
    feature_cols = json.load(f)

# Preparar datos del municipio para predicción
def predecir_delitos_anuales(municipio_data: dict) -> float:
    """Predice delitos anuales para un municipio."""
    X = pd.DataFrame([municipio_data])[feature_cols]
    X_scaled = scaler.transform(X)
    prediccion = model.predict(X_scaled)[0]
    return max(0, prediccion)  # No puede ser negativo

# Ejemplo
prediccion = predecir_delitos_anuales({
    'poblacion_total': 50000,
    'densidad_poblacional': 120,
    'lag_1_anio': 150,
    # ... otras features
})
print(f"Predicción: {prediccion:.0f} delitos")
```

**Componentes sugeridos:**
- **Tarjetas KPI**: Predicción para el próximo año
- **Comparativo**: Predicción vs año actual
- **Semáforos**: Verde/Amarillo/Rojo según variación

---

## 🤖 Integración en Chatbot

### 1. Estructura de Respuestas Pre-generadas

El modelo descriptivo incluye descripciones textuales listas para chatbot:

```python
import json

# Cargar perfiles
with open('models/descriptivo/annual/perfiles_municipios_{timestamp}.json', 'r') as f:
    perfiles = json.load(f)

def responder_sobre_municipio(codigo_municipio: str) -> str:
    """Genera respuesta sobre un municipio específico."""
    if codigo_municipio in perfiles:
        return perfiles[codigo_municipio]['descripcion']
    return "No tengo información sobre ese municipio."

# Ejemplo de uso
print(responder_sobre_municipio('68001'))
```

**Respuesta ejemplo:**
> "El municipio 68001 pertenece al grupo 'Alto Riesgo - Urbano'. Presenta un nivel de criminalidad alto con un promedio de 2,450 delitos anuales, con tendencia ASCENDENTE (+12.5% en el periodo). El delito predominante es HURTOS (45.2% del total). Población: 580,000 habitantes. Densidad: 2,150 hab/km²."

### 2. Preguntas Frecuentes y Respuestas

```python
def chatbot_annual(pregunta: str, perfiles: dict, clusters: dict) -> str:
    """Procesa preguntas sobre datos anuales."""
    pregunta = pregunta.lower()
    
    # Pregunta: municipios de alto riesgo
    if 'alto riesgo' in pregunta or 'peligroso' in pregunta:
        alto_riesgo = [p for p in perfiles.values() 
                       if 'Alto Riesgo' in p.get('cluster_nombre', '')]
        return f"Hay {len(alto_riesgo)} municipios clasificados como Alto Riesgo: " + \
               ", ".join([str(p['codigo_municipio']) for p in alto_riesgo[:5]]) + "..."
    
    # Pregunta: tendencia de un municipio
    if 'tendencia' in pregunta:
        # Extraer código de municipio de la pregunta
        for cod, perfil in perfiles.items():
            if cod in pregunta:
                return f"El municipio {cod} tiene tendencia {perfil['tendencia']} " + \
                       f"con una pendiente de {perfil['pendiente_anual']:.1f} delitos/año."
    
    # Pregunta: delito predominante
    if 'delito' in pregunta and ('principal' in pregunta or 'predominante' in pregunta):
        for cod, perfil in perfiles.items():
            if cod in pregunta:
                return f"En el municipio {cod}, el delito predominante es " + \
                       f"{perfil['delito_dominante']} ({perfil['prop_delito_dominante']:.1f}% del total)."
    
    # Pregunta: clusters disponibles
    if 'cluster' in pregunta or 'grupo' in pregunta:
        grupos = [c['nombre'] for c in clusters.values()]
        return f"Los municipios están agrupados en {len(grupos)} clusters: " + ", ".join(grupos)
    
    return "No entendí la pregunta. Puedo responder sobre tendencias, clusters, " + \
           "municipios de alto riesgo y composición delictiva."
```

### 3. Ejemplos de Interacción

| Pregunta del Usuario | Respuesta del Chatbot |
|---------------------|----------------------|
| "¿Cuáles son los municipios de alto riesgo?" | "Hay 15 municipios clasificados como Alto Riesgo: 68001, 68081, 68276..." |
| "¿Cuál es la tendencia del municipio 68001?" | "El municipio 68001 tiene tendencia Ascendente con una pendiente de 45.2 delitos/año." |
| "¿Cuántos delitos habrá el próximo año en 68001?" | "Según el modelo predictivo, se estiman 2,580 delitos para el próximo año en el municipio 68001." |
| "¿Qué grupos de municipios existen?" | "Los municipios están agrupados en 4 clusters: Alto Riesgo - Urbano, Riesgo Medio, Bajo Riesgo - Rural, Estable." |
| "Describe la situación del municipio 68307" | "El municipio 68307 pertenece al grupo 'Bajo Riesgo - Rural'..." |

### 4. Combinando Descriptivo + Predictivo

```python
def respuesta_completa(codigo_municipio: str) -> str:
    """Combina información descriptiva con predicción."""
    
    # Información descriptiva
    perfil = perfiles.get(codigo_municipio)
    if not perfil:
        return "Municipio no encontrado."
    
    # Predicción
    prediccion = predecir_delitos_anuales(obtener_features_municipio(codigo_municipio))
    
    respuesta = f"""
    **{perfil['cluster_nombre']}**
    
    📊 **Situación Actual:**
    - Promedio histórico: {perfil['delitos_promedio']:.0f} delitos/año
    - Tendencia: {perfil['tendencia']}
    - Delito principal: {perfil['delito_dominante']}
    
    🔮 **Predicción:**
    - Próximo año: {prediccion:.0f} delitos estimados
    - Variación esperada: {((prediccion/perfil['delitos_promedio'])-1)*100:+.1f}%
    """
    return respuesta
```

---

## 📊 Métricas del Modelo Predictivo

```python
# Leer metadata del modelo
with open('models/predictivos/regression_annual/metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Modelo: {metadata['model_type']}")
print(f"MAE: {metadata['metrics']['MAE']:.2f} delitos")
print(f"RMSE: {metadata['metrics']['RMSE']:.2f} delitos")
print(f"R²: {metadata['metrics']['R2']:.4f}")
print(f"MAPE: {metadata['metrics']['MAPE']:.2f}%")
```

---

## 🔄 Actualización de Datos

1. **Ejecutar notebook descriptivo**: Genera nuevos JSONs con timestamp
2. **Ejecutar notebook predictivo**: Re-entrena modelo con datos nuevos
3. **Actualizar rutas en dashboard/chatbot**: Apuntar a archivos más recientes

```python
from pathlib import Path
import glob

# Obtener archivo más reciente
def obtener_ultimo_archivo(patron: str) -> str:
    archivos = glob.glob(patron)
    return max(archivos, key=lambda x: Path(x).stat().st_mtime)

ultimo_perfil = obtener_ultimo_archivo('models/descriptivo/annual/perfiles_municipios_*.json')
```

---

## 📝 Notas Importantes

1. **Modelo Descriptivo**: Ideal para consultas frecuentes y respuestas instantáneas
2. **Modelo Predictivo**: Usar para proyecciones específicas cuando el usuario lo solicite
3. **Clusters**: Actualizar si cambian significativamente los patrones de criminalidad
4. **Timestamps**: Los archivos descriptivos incluyen timestamp para control de versiones
