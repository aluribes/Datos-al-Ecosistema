# Modelo de Clustering Geoespacial-Delictivo: Guia de Uso

Este documento explica como utilizar el modelo de clustering de municipios para el tablero web y el chatbot.

---

## Descripcion General

| Aspecto | Detalle |
|---------|---------|
| **Tipo de modelo** | Clustering no supervisado (KMeans) |
| **Objetivo** | Agrupar municipios segun comportamiento delictivo y caracteristicas geograficas |
| **Entrada** | Tasas de delitos, densidad poblacional, area, proporciones demograficas |
| **Salida** | Asignacion de cluster (0, 1, 2, ...) para cada municipio |

---

## Ubicacion de Archivos

### Modelo Predictivo
```
models/clustering/geo_municipal/
├── kmeans_geo_municipal.joblib    # Modelo KMeans entrenado
├── scaler.joblib                   # RobustScaler para normalizar datos
├── pca_2d.joblib                   # PCA para visualizacion 2D
├── metadata.json                   # Configuracion y metricas
├── municipios_clusters.parquet     # Resultados (formato Parquet)
└── municipios_clusters.csv         # Resultados (formato CSV)
```

### Modelo Descriptivo (para consultas rapidas)
```
models/descriptivo/clustering_geo/
├── perfiles_clusters.json          # Estadisticas por cluster
├── asignacion_municipios.json      # Cluster de cada municipio
└── respuestas_chatbot.json         # Respuestas pre-calculadas
```

---

## Estructura de los Archivos JSON

### 1. `asignacion_municipios.json`
Contiene la asignacion de cluster para cada municipio.

```json
{
  "68001": {
    "municipio": "BUCARAMANGA",
    "cluster": 2,
    "tasa_delitos": 1250.5,
    "densidad": 2500.3
  },
  "68081": {
    "municipio": "BARRANCABERMEJA",
    "cluster": 1,
    "tasa_delitos": 890.2,
    "densidad": 180.5
  }
}
```

### 2. `perfiles_clusters.json`
Estadisticas agregadas por cada cluster.

```json
{
  "0": {
    "n_municipios": 45,
    "municipios": ["AGUADA", "ALBANIA", "..."],
    "codigos": [68013, 68020, ...],
    "estadisticas": {
      "tasa_delitos_promedio": 85.3,
      "densidad_promedio": 25.8,
      "poblacion_promedio": 8500,
      "area_promedio_km2": 450.2
    }
  },
  "1": {
    "n_municipios": 25,
    "municipios": [...],
    "estadisticas": {...}
  }
}
```

### 3. `respuestas_chatbot.json`
Respuestas pre-calculadas para consultas frecuentes.

```json
{
  "pregunta_cluster_municipio": "Usa asignacion_municipios.json con el codigo del municipio",
  "pregunta_municipios_similares": "Busca en perfiles_clusters.json el cluster del municipio",
  "pregunta_cluster_mas_peligroso": {
    "cluster": 2,
    "tasa_promedio": 1250.5
  },
  "pregunta_cluster_mas_seguro": {
    "cluster": 0,
    "tasa_promedio": 85.3
  }
}
```

---

## Uso en el Chatbot

### Preguntas que puede responder

| Pregunta del usuario | Archivo a usar | Campo |
|---------------------|----------------|-------|
| "A que grupo pertenece [municipio]?" | `asignacion_municipios.json` | `[codigo].cluster` |
| "Que municipios son similares a [municipio]?" | `perfiles_clusters.json` | `[cluster].municipios` |
| "Cual es el grupo mas peligroso?" | `respuestas_chatbot.json` | `pregunta_cluster_mas_peligroso` |
| "Cual es el grupo mas seguro?" | `respuestas_chatbot.json` | `pregunta_cluster_mas_seguro` |
| "Cuantos municipios hay en cada grupo?" | `perfiles_clusters.json` | `[cluster].n_municipios` |

### Implementacion en Python

```python
import json
from pathlib import Path

# Cargar datos
MODEL_PATH = Path('models/descriptivo/clustering_geo/')

with open(MODEL_PATH / 'asignacion_municipios.json', 'r', encoding='utf-8') as f:
    asignacion = json.load(f)

with open(MODEL_PATH / 'perfiles_clusters.json', 'r', encoding='utf-8') as f:
    perfiles = json.load(f)

with open(MODEL_PATH / 'respuestas_chatbot.json', 'r', encoding='utf-8') as f:
    respuestas = json.load(f)


def responder_clustering(pregunta: str, codigo_municipio: int = None) -> str:
    """
    Responde preguntas sobre clustering de municipios.
    
    Args:
        pregunta: Texto de la pregunta del usuario
        codigo_municipio: Codigo DANE del municipio (opcional)
    
    Returns:
        Respuesta en texto
    """
    pregunta = pregunta.lower()
    
    # Pregunta sobre un municipio especifico
    if codigo_municipio and str(codigo_municipio) in asignacion:
        mun = asignacion[str(codigo_municipio)]
        cluster_id = mun['cluster']
        
        if 'grupo' in pregunta or 'cluster' in pregunta or 'pertenece' in pregunta:
            return f"{mun['municipio']} pertenece al Grupo {cluster_id}."
        
        elif 'similar' in pregunta or 'parecido' in pregunta:
            perfil = perfiles[str(cluster_id)]
            otros = [m for m in perfil['municipios'] if m != mun['municipio']][:5]
            return f"Municipios similares a {mun['municipio']}: {', '.join(otros)}."
        
        elif 'caracteristica' in pregunta or 'perfil' in pregunta:
            perfil = perfiles[str(cluster_id)]
            stats = perfil['estadisticas']
            return (f"{mun['municipio']} (Grupo {cluster_id}): "
                    f"Tasa promedio de delitos: {stats['tasa_delitos_promedio']:.1f}, "
                    f"Densidad: {stats['densidad_promedio']:.1f} hab/km2.")
    
    # Preguntas generales
    if 'peligroso' in pregunta or 'mas delitos' in pregunta:
        info = respuestas['pregunta_cluster_mas_peligroso']
        return f"El Grupo {info['cluster']} es el mas peligroso con una tasa promedio de {info['tasa_promedio']:.1f} delitos por 100k hab."
    
    elif 'seguro' in pregunta or 'menos delitos' in pregunta:
        info = respuestas['pregunta_cluster_mas_seguro']
        return f"El Grupo {info['cluster']} es el mas seguro con una tasa promedio de {info['tasa_promedio']:.1f} delitos por 100k hab."
    
    elif 'cuantos grupos' in pregunta or 'cuantos cluster' in pregunta:
        return f"Hay {len(perfiles)} grupos de municipios."
    
    elif 'cuantos municipios' in pregunta:
        resumen = [f"Grupo {k}: {v['n_municipios']} municipios" for k, v in perfiles.items()]
        return "Distribucion: " + ", ".join(resumen)
    
    return "No tengo informacion especifica sobre esa pregunta de clustering."


# Ejemplo de uso
print(responder_clustering("A que grupo pertenece?", codigo_municipio=68001))
print(responder_clustering("Que municipios son similares?", codigo_municipio=68001))
print(responder_clustering("Cual es el grupo mas peligroso?"))
```

---

## Uso en el Tablero Web

### Visualizaciones Recomendadas

| Visualizacion | Archivo | Campos |
|--------------|---------|--------|
| **Mapa de clusters** | `asignacion_municipios.json` | `[codigo].cluster` |
| **Tabla de municipios** | `municipios_clusters.csv` | Todos |
| **KPIs por cluster** | `perfiles_clusters.json` | `estadisticas` |
| **Grafico de barras** | `perfiles_clusters.json` | `n_municipios` |

### Colores sugeridos por cluster

```javascript
const coloresCluster = {
  0: '#22c55e',  // Verde - Bajo riesgo
  1: '#eab308',  // Amarillo - Riesgo medio-bajo
  2: '#f97316',  // Naranja - Riesgo medio-alto
  3: '#ef4444',  // Rojo - Alto riesgo
  4: '#7c3aed'   // Morado - Muy alto riesgo
};
```

### Ejemplo: Mapa con Leaflet/Mapbox

```javascript
// Cargar datos
const asignacion = await fetch('/api/clustering/asignacion_municipios.json').then(r => r.json());

// Funcion para obtener color del municipio
function getColorMunicipio(codigoMunicipio) {
  const mun = asignacion[codigoMunicipio];
  if (!mun) return '#gray';
  return coloresCluster[mun.cluster] || '#gray';
}

// Funcion para tooltip
function getTooltip(codigoMunicipio) {
  const mun = asignacion[codigoMunicipio];
  if (!mun) return 'Sin datos';
  
  return `
    <strong>${mun.municipio}</strong><br/>
    Grupo: ${mun.cluster}<br/>
    Tasa de delitos: ${mun.tasa_delitos.toFixed(1)}<br/>
    Densidad: ${mun.densidad.toFixed(1)} hab/km2
  `;
}

// Aplicar a capa GeoJSON
geojsonLayer.eachLayer(function(layer) {
  const codigo = layer.feature.properties.codigo_municipio;
  layer.setStyle({ fillColor: getColorMunicipio(codigo) });
  layer.bindTooltip(getTooltip(codigo));
});
```

### Ejemplo: KPIs en React

```jsx
import { useEffect, useState } from 'react';

function ClusterKPIs() {
  const [perfiles, setPerfiles] = useState(null);
  
  useEffect(() => {
    fetch('/api/clustering/perfiles_clusters.json')
      .then(r => r.json())
      .then(setPerfiles);
  }, []);
  
  if (!perfiles) return <div>Cargando...</div>;
  
  return (
    <div className="grid grid-cols-4 gap-4">
      {Object.entries(perfiles).map(([clusterId, data]) => (
        <div key={clusterId} className="p-4 rounded-lg bg-white shadow">
          <h3 className="text-lg font-bold">Grupo {clusterId}</h3>
          <p className="text-3xl font-bold">{data.n_municipios}</p>
          <p className="text-sm text-gray-500">municipios</p>
          <div className="mt-2 text-sm">
            <p>Tasa delitos: {data.estadisticas.tasa_delitos_promedio.toFixed(1)}</p>
            <p>Densidad: {data.estadisticas.densidad_promedio.toFixed(1)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## Uso del Modelo Predictivo (Avanzado)

Para asignar nuevos municipios o actualizar clusters, usar el modelo `.joblib`:

```python
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# Cargar modelo y artefactos
MODEL_PATH = Path('models/clustering/geo_municipal/')

model = joblib.load(MODEL_PATH / 'kmeans_geo_municipal.joblib')
scaler = joblib.load(MODEL_PATH / 'scaler.joblib')

# Cargar metadata para obtener features
import json
with open(MODEL_PATH / 'metadata.json', 'r') as f:
    metadata = json.load(f)

FEATURE_COLS = metadata['features']


def asignar_cluster(datos_municipio: dict) -> int:
    """
    Asigna un cluster a un municipio basado en sus caracteristicas.
    
    Args:
        datos_municipio: Diccionario con las features requeridas
        
    Returns:
        ID del cluster asignado
    """
    # Crear DataFrame
    X = pd.DataFrame([datos_municipio])[FEATURE_COLS]
    
    # Escalar
    X_scaled = scaler.transform(X)
    
    # Predecir cluster
    cluster = model.predict(X_scaled)[0]
    
    return int(cluster)


# Ejemplo: asignar cluster a un municipio con datos actualizados
nuevo_municipio = {
    'total_delitos_tasa': 150.5,
    'HURTOS_tasa': 45.2,
    'LESIONES_tasa': 30.1,
    'VIOLENCIA INTRAFAMILIAR_tasa': 25.3,
    'HOMICIDIOS_tasa': 5.2,
    'AMENAZAS_tasa': 15.8,
    'log_densidad': np.log(100),
    'log_area': np.log(500),
    'centros_por_km2': 0.01,
    'proporcion_menores': 0.20,
    'proporcion_adultos': 0.75,
    'proporcion_adolescentes': 0.05
}

cluster_asignado = asignar_cluster(nuevo_municipio)
print(f"Cluster asignado: {cluster_asignado}")
```

---

## Interpretacion de Clusters

Los clusters representan grupos de municipios con caracteristicas similares:

| Cluster | Interpretacion Tipica | Caracteristicas |
|---------|----------------------|-----------------|
| 0 | Rural con baja criminalidad | Baja densidad, baja tasa de delitos, area grande |
| 1 | Semi-rural con criminalidad media | Densidad media, tasa moderada |
| 2 | Urbano con alta criminalidad | Alta densidad, alta tasa de delitos |
| 3 | Cabeceras municipales | Muy alta densidad, concentracion de delitos |

**Nota**: La interpretacion exacta depende de los datos. Revisar `perfiles_clusters.json` para detalles especificos.

---

## API Endpoints Sugeridos

```python
# FastAPI ejemplo
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/api/clustering/municipio/{codigo}")
async def get_cluster_municipio(codigo: int):
    """Obtiene el cluster de un municipio."""
    if str(codigo) in asignacion:
        return asignacion[str(codigo)]
    return {"error": "Municipio no encontrado"}

@app.get("/api/clustering/cluster/{cluster_id}")
async def get_perfil_cluster(cluster_id: int):
    """Obtiene el perfil de un cluster."""
    if str(cluster_id) in perfiles:
        return perfiles[str(cluster_id)]
    return {"error": "Cluster no encontrado"}

@app.get("/api/clustering/similares/{codigo}")
async def get_municipios_similares(codigo: int, limit: int = 5):
    """Obtiene municipios similares."""
    if str(codigo) not in asignacion:
        return {"error": "Municipio no encontrado"}
    
    cluster_id = asignacion[str(codigo)]['cluster']
    municipio_actual = asignacion[str(codigo)]['municipio']
    
    similares = [
        m for m in perfiles[str(cluster_id)]['municipios']
        if m != municipio_actual
    ][:limit]
    
    return {"municipio": municipio_actual, "similares": similares}
```

---

## Metricas del Modelo

Las metricas de evaluacion se encuentran en `metadata.json`:

| Metrica | Descripcion | Rango | Mejor |
|---------|-------------|-------|-------|
| Silhouette Score | Cohesion vs separacion | -1 a 1 | Mayor |
| Calinski-Harabasz | Varianza entre/dentro clusters | 0 a inf | Mayor |
| Davies-Bouldin | Similitud promedio entre clusters | 0 a inf | Menor |

---

## Resumen de Archivos

| Archivo | Uso | Formato |
|---------|-----|---------|
| `asignacion_municipios.json` | Consulta rapida por municipio | JSON |
| `perfiles_clusters.json` | Estadisticas agregadas | JSON |
| `respuestas_chatbot.json` | Respuestas pre-calculadas | JSON |
| `municipios_clusters.csv` | Tabla completa | CSV |
| `kmeans_geo_municipal.joblib` | Modelo para prediccion | Joblib |
| `scaler.joblib` | Normalizador de features | Joblib |
| `metadata.json` | Configuracion y metricas | JSON |
