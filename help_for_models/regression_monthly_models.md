# Guía de Uso: Modelos de Regresión Mensual de Delitos

## Descripción General

Este documento describe cómo integrar los modelos de regresión mensual de delitos en **tableros de visualización (dashboards)** y **chatbots** para análisis de seguridad en Santander.

Se utilizan dos modelos complementarios:
- **Modelo Descriptivo**: Estadísticas pre-calculadas con respuestas instantáneas
- **Modelo Predictivo**: Predicción de delitos mensuales por municipio

---

## 📁 Archivos Generados

### Modelo Descriptivo (`models/descriptivo/regression_monthly/`)

| Archivo | Descripción |
|---------|-------------|
| `estadisticas_generales.json` | Métricas globales del dataset |
| `estadisticas_por_municipio.json` | Análisis detallado por municipio |
| `tendencias_temporales.json` | Patrones por año y mes (estacionalidad) |
| `comparativas.json` | Rankings y comparaciones entre municipios |
| `respuestas_chatbot.json` | Respuestas pre-generadas para preguntas frecuentes |

### Modelo Predictivo (`models/predictivos/regression_monthly/`)

| Archivo | Descripción |
|---------|-------------|
| `xgb_regressor.joblib` | Modelo XGBoost entrenado |
| `scaler.joblib` | Escalador para preprocesamiento |
| `feature_columns.json` | Lista de features del modelo |
| `metadata.json` | Métricas y configuración del modelo |

---

## 🖥️ Integración en Tableros (Dashboard)

### 1. Panel de Estadísticas Generales

```python
import json

# Cargar estadísticas generales
with open('models/descriptivo/regression_monthly/estadisticas_generales.json', 'r') as f:
    stats = json.load(f)

# Datos para KPIs
print(f"Total delitos histórico: {stats['delitos_historico']['total_acumulado']:,}")
print(f"Promedio mensual: {stats['delitos_historico']['promedio_mensual_global']:.0f}")
print(f"Último año - Total: {stats['delitos_ultimo_anio']['total']:,}")
print(f"Variación interanual: {stats['delitos_ultimo_anio']['variacion_vs_anterior']}%")
```

**Componentes sugeridos:**
- **Tarjetas KPI**: Total delitos, promedio mensual, variación %
- **Indicador de tendencia**: Flecha arriba/abajo según variación
- **Contador de registros**: Total municipios, período cubierto

### 2. Rankings de Municipios

```python
# Cargar comparativas
with open('models/descriptivo/regression_monthly/comparativas.json', 'r') as f:
    comparativas = json.load(f)

# Top municipios con más delitos
print("Top 10 municipios por delitos:")
for i, mun in enumerate(comparativas['ranking_total_delitos'][:10], 1):
    print(f"  {i}. {mun['codigo_municipio']}: {mun['total_delitos']:,} delitos")

# Municipios con mayor incremento
print("\nMunicipios con mayor incremento:")
for mun in comparativas['mayor_incremento'][:5]:
    print(f"  - {mun['codigo_municipio']}: +{mun['incremento_pct']:.1f}%")
```

**Componentes sugeridos:**
- **Tabla ranking**: Top 10 municipios ordenados por delitos
- **Mapa de calor**: Colorear municipios por volumen de delitos
- **Comparativo barras**: Municipio seleccionado vs promedio departamental

### 3. Análisis de Estacionalidad

```python
# Cargar tendencias temporales
with open('models/descriptivo/regression_monthly/tendencias_temporales.json', 'r') as f:
    tendencias = json.load(f)

# Patrón mensual (estacionalidad)
print("Delitos promedio por mes:")
for mes, datos in tendencias['por_mes'].items():
    barra = '█' * int(datos['promedio'] / 100)
    print(f"  Mes {mes:>2}: {barra} {datos['promedio']:.0f}")

# Evolución anual
print("\nEvolución por año:")
for anio, datos in tendencias['por_anio'].items():
    print(f"  {anio}: {datos['total']:,} delitos")
```

**Componentes sugeridos:**
- **Gráfico de líneas**: Evolución mensual histórica
- **Heatmap**: Año vs Mes con intensidad de color
- **Boxplot por mes**: Distribución estacional

### 4. Predicciones Mensuales

```python
import joblib
import pandas as pd
import json

# Cargar modelo predictivo
model = joblib.load('models/predictivos/regression_monthly/xgb_regressor.joblib')
scaler = joblib.load('models/predictivos/regression_monthly/scaler.joblib')

with open('models/predictivos/regression_monthly/feature_columns.json', 'r') as f:
    feature_cols = json.load(f)

def predecir_delitos_mensuales(municipio_data: dict) -> float:
    """Predice delitos para el próximo mes."""
    X = pd.DataFrame([municipio_data])[feature_cols]
    X_scaled = scaler.transform(X)
    prediccion = model.predict(X_scaled)[0]
    return max(0, prediccion)

# Ejemplo
prediccion = predecir_delitos_mensuales({
    'codigo_municipio': 68001,
    'mes': 3,
    'poblacion_total': 580000,
    'lag_1': 2100,  # Delitos del mes anterior
    'lag_3': 2050,  # Delitos hace 3 meses
    'roll_mean_3': 2080,  # Media móvil 3 meses
    # ... otras features
})
print(f"Predicción: {prediccion:.0f} delitos")
```

**Componentes sugeridos:**
- **Selector de municipio**: Dropdown para elegir municipio
- **Gráfico de forecast**: Histórico + predicción próximos meses
- **Intervalos de confianza**: Banda de incertidumbre

---

## 🤖 Integración en Chatbot

### 1. Respuestas Pre-generadas

El modelo descriptivo incluye respuestas listas para uso:

```python
import json

# Cargar respuestas pre-generadas
with open('models/descriptivo/regression_monthly/respuestas_chatbot.json', 'r') as f:
    respuestas = json.load(f)

def obtener_respuesta(categoria: str, subcategoria: str = None) -> str:
    """Obtiene respuesta pre-generada."""
    if subcategoria:
        return respuestas.get(categoria, {}).get(subcategoria, "Sin información.")
    return respuestas.get(categoria, "Sin información.")

# Ejemplos
print(obtener_respuesta('resumen_general'))
print(obtener_respuesta('estacionalidad', 'mes_mas_delitos'))
print(obtener_respuesta('rankings', 'top_5'))
```

### 2. Handler de Preguntas Mensuales

```python
def chatbot_monthly(pregunta: str, stats: dict, comparativas: dict, tendencias: dict) -> str:
    """Procesa preguntas sobre datos mensuales."""
    pregunta = pregunta.lower()
    
    # Pregunta: promedio mensual
    if 'promedio' in pregunta and 'mensual' in pregunta:
        promedio = stats['delitos_historico']['promedio_mensual_global']
        return f"El promedio mensual histórico de delitos es de {promedio:.0f} delitos."
    
    # Pregunta: mes con más delitos
    if 'mes' in pregunta and ('más' in pregunta or 'mayor' in pregunta):
        mes_max = max(tendencias['por_mes'].items(), key=lambda x: x[1]['promedio'])
        return f"El mes con más delitos es {mes_max[0]} con un promedio de {mes_max[1]['promedio']:.0f} delitos."
    
    # Pregunta: variación este año
    if 'variación' in pregunta or 'cambio' in pregunta:
        variacion = stats['delitos_ultimo_anio']['variacion_vs_anterior']
        direccion = "aumentaron" if variacion > 0 else "disminuyeron"
        return f"Respecto al año anterior, los delitos {direccion} un {abs(variacion):.1f}%."
    
    # Pregunta: municipio con más delitos
    if 'municipio' in pregunta and ('más' in pregunta or 'mayor' in pregunta):
        top = comparativas['ranking_total_delitos'][0]
        return f"El municipio con más delitos es {top['codigo_municipio']} " + \
               f"con {top['total_delitos']:,} delitos acumulados."
    
    # Pregunta: cuántos delitos el mes pasado
    if 'mes pasado' in pregunta or 'último mes' in pregunta:
        ultimo = stats['delitos_ultimo_mes']
        return f"El último mes registrado tuvo {ultimo['total']:,} delitos."
    
    # Pregunta: tendencia
    if 'tendencia' in pregunta:
        variacion = stats['delitos_ultimo_anio']['variacion_vs_anterior']
        if variacion > 5:
            return "La tendencia es ASCENDENTE. Los delitos han aumentado significativamente."
        elif variacion < -5:
            return "La tendencia es DESCENDENTE. Los delitos han disminuido."
        else:
            return "La tendencia es ESTABLE. Los delitos se mantienen similares al año anterior."
    
    return "Puedo responder sobre promedios mensuales, estacionalidad, " + \
           "rankings de municipios, tendencias y variaciones."
```

### 3. Ejemplos de Interacción

| Pregunta del Usuario | Respuesta del Chatbot |
|---------------------|----------------------|
| "¿Cuál es el promedio mensual de delitos?" | "El promedio mensual histórico de delitos es de 2,150 delitos." |
| "¿Qué mes tiene más delitos?" | "El mes con más delitos es Marzo con un promedio de 2,480 delitos." |
| "¿Cómo cambió la criminalidad este año?" | "Respecto al año anterior, los delitos aumentaron un 3.2%." |
| "¿Cuál municipio tiene más delitos?" | "El municipio con más delitos es 68001 con 45,230 delitos acumulados." |
| "¿Cuántos delitos hubo el mes pasado?" | "El último mes registrado tuvo 2,315 delitos." |
| "Predice los delitos del próximo mes en 68001" | "Según el modelo predictivo, se estiman 2,180 delitos para el próximo mes en el municipio 68001." |

### 4. Predicción bajo Demanda

```python
def predecir_para_chatbot(codigo_municipio: str, mes: int = None) -> str:
    """Genera predicción formateada para chatbot."""
    import datetime
    
    # Si no se especifica mes, usar el siguiente
    if mes is None:
        mes = datetime.datetime.now().month % 12 + 1
    
    # Obtener datos del municipio
    municipio_data = obtener_datos_municipio(codigo_municipio, mes)
    
    if municipio_data is None:
        return f"No tengo datos suficientes para el municipio {codigo_municipio}."
    
    # Predecir
    prediccion = predecir_delitos_mensuales(municipio_data)
    
    # Comparar con histórico
    promedio_historico = estadisticas_municipio[codigo_municipio]['promedio_mensual']
    variacion = ((prediccion / promedio_historico) - 1) * 100
    
    nombre_mes = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][mes-1]
    
    respuesta = f"📊 **Predicción para {nombre_mes}** en municipio {codigo_municipio}:\n\n"
    respuesta += f"- Delitos estimados: **{prediccion:.0f}**\n"
    respuesta += f"- Promedio histórico: {promedio_historico:.0f}\n"
    respuesta += f"- Variación esperada: {variacion:+.1f}%\n"
    
    if variacion > 10:
        respuesta += "\n⚠️ Se prevé un incremento significativo. Revisar asignación de recursos."
    elif variacion < -10:
        respuesta += "\n✅ Se prevé una reducción. Tendencia positiva."
    
    return respuesta
```

### 5. Combinando Descriptivo + Predictivo

```python
def respuesta_completa_mensual(codigo_municipio: str) -> str:
    """Combina estadísticas históricas con predicción."""
    
    # Cargar estadísticas del municipio
    with open('models/descriptivo/regression_monthly/estadisticas_por_municipio.json', 'r') as f:
        municipios = json.load(f)
    
    if codigo_municipio not in municipios:
        return "Municipio no encontrado."
    
    stats = municipios[codigo_municipio]
    
    # Generar predicción
    prediccion = predecir_delitos_mensuales(obtener_features_municipio(codigo_municipio))
    
    respuesta = f"""
    📍 **Municipio {codigo_municipio}**
    
    📈 **Estadísticas Históricas:**
    - Total acumulado: {stats['total_delitos']:,} delitos
    - Promedio mensual: {stats['promedio_mensual']:.0f}
    - Tendencia: {stats['tendencia']}
    - Mes más crítico: {stats['mes_mayor_promedio']}
    
    🔮 **Predicción Próximo Mes:**
    - Estimación: {prediccion:.0f} delitos
    - Intervalo: [{prediccion*0.85:.0f} - {prediccion*1.15:.0f}]
    
    📊 **Comparación Departamental:**
    - Ranking: #{stats['ranking_departamental']} de 87 municipios
    - {stats['porcentaje_departamento']:.1f}% del total departamental
    """
    return respuesta
```

---

## 📊 Métricas del Modelo Predictivo

```python
# Leer metadata del modelo
with open('models/predictivos/regression_monthly/metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Modelo: {metadata['model_type']}")
print(f"Features: {metadata['n_features']}")
print(f"MAE: {metadata['metrics']['MAE']:.2f} delitos")
print(f"RMSE: {metadata['metrics']['RMSE']:.2f} delitos")
print(f"R²: {metadata['metrics']['R2']:.4f}")
print(f"MAPE: {metadata['metrics']['MAPE']:.2f}%")
```

---

## 🔄 Flujo de Actualización

### Mensualmente:
1. Ejecutar `02_process_socrata.py` para obtener nuevos datos
2. Ejecutar `04_generate_regression_monthly_dataset.py` para actualizar dataset
3. Ejecutar notebook descriptivo (`05_regression_monthly_descript.ipynb`)
4. Ejecutar notebook predictivo (`05_regression_monthly_predict.ipynb`)

### En el Dashboard/Chatbot:
```python
from pathlib import Path
import glob

def cargar_ultimo_modelo():
    """Carga la versión más reciente de los modelos."""
    base = Path('models/descriptivo/regression_monthly')
    
    # Obtener archivos más recientes por patrón
    archivos = {
        'stats': sorted(base.glob('estadisticas_generales_*.json'))[-1],
        'municipios': sorted(base.glob('estadisticas_por_municipio_*.json'))[-1],
        'tendencias': sorted(base.glob('tendencias_temporales_*.json'))[-1],
    }
    return archivos
```

---

## 📝 Notas Importantes

1. **Lags Temporales**: El modelo predictivo requiere `lag_1`, `lag_3`, `lag_12` - delitos de meses anteriores
2. **Rolling Windows**: Se necesitan `roll_mean_3`, `roll_mean_12` para capturar tendencias
3. **Estacionalidad**: El mes actual afecta significativamente la predicción
4. **Actualización**: Los datos deben actualizarse mensualmente para mantener precisión
5. **Intervalo de Confianza**: Considerar ±15% como margen de error típico

---

## 🎯 Casos de Uso

| Escenario | Modelo Recomendado | Datos a Usar |
|-----------|-------------------|--------------|
| "¿Cuántos delitos hubo el año pasado?" | Descriptivo | `estadisticas_generales.json` |
| "¿Cuál es el mes más peligroso?" | Descriptivo | `tendencias_temporales.json` |
| "¿Cuántos delitos habrá el próximo mes?" | Predictivo | `xgb_regressor.joblib` |
| "Comparar municipios por criminalidad" | Descriptivo | `comparativas.json` |
| "Alerta si supera umbral" | Ambos | Predicción + Histórico |
