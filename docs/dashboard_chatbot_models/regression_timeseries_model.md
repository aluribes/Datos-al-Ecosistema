# Guía de Uso: Modelo de Forecast de Series Temporales

## Descripción General

Este documento describe cómo integrar el modelo de **forecast de series temporales** basado en Prophet para predecir la evolución mensual de delitos en Santander.

A diferencia de los modelos de regresión por municipio, este modelo:
- **Agrega todos los delitos del departamento** en una única serie temporal
- **Predice la tendencia general** de criminalidad a nivel departamental
- **Captura patrones estacionales** anuales

---

## 📁 Archivos Generados

### Modelo de Forecast (`models/timeserie/regression_timeseries/`)

| Archivo | Descripción |
|---------|-------------|
| `prophet_model.joblib` | Modelo Prophet entrenado |
| `forecast_futuro.csv` | Predicciones para los próximos 12 meses |
| `metadata.json` | Configuración, métricas y parámetros del modelo |

---

## 🖥️ Integración en Tableros (Dashboard)

### 1. Visualización del Forecast

```python
import pandas as pd
import joblib
import json

# Cargar forecast pre-generado
forecast = pd.read_csv('models/timeserie/regression_timeseries/forecast_futuro.csv')
forecast['ds'] = pd.to_datetime(forecast['ds'])

# Datos para gráfico
print("Forecast para los próximos 12 meses:")
for _, row in forecast.iterrows():
    print(f"  {row['ds'].strftime('%Y-%m')}: {row['yhat']:.0f} " + 
          f"(IC: {row['yhat_lower']:.0f} - {row['yhat_upper']:.0f})")
```

**Componentes sugeridos:**
- **Gráfico de líneas**: Serie histórica + forecast futuro
- **Banda de confianza**: Área sombreada con intervalo de confianza
- **Indicadores KPI**: Predicción promedio, máximo esperado, mínimo esperado

### 2. Panel de Tendencia General

```python
# Cargar metadata
with open('models/timeserie/regression_timeseries/metadata.json', 'r') as f:
    metadata = json.load(f)

# Información de tendencia
print(f"Período de entrenamiento: {metadata['training_data']['start']} a {metadata['training_data']['end']}")
print(f"Meses de forecast: {metadata['forecast']['months']}")
print(f"Predicción promedio: {metadata['forecast']['mean_prediction']:.0f} delitos/mes")

# Métricas del modelo
print(f"\nPrecisión del modelo:")
print(f"  MAE: {metadata['metrics']['MAE']:.2f} delitos")
print(f"  MAPE: {metadata['metrics']['MAPE']:.2f}%")
```

**Componentes sugeridos:**
- **Tarjetas de resumen**: Tendencia (↑↓→), predicción promedio
- **Indicador de estacionalidad**: Meses altos vs bajos
- **Comparativo**: Este año vs proyección

### 3. Descomposición de la Serie

```python
import joblib

# Cargar modelo
model = joblib.load('models/timeserie/regression_timeseries/prophet_model.joblib')

# Generar componentes del modelo
future = model.make_future_dataframe(periods=12, freq='MS')
forecast_completo = model.predict(future)

# Componentes disponibles
componentes = ['trend', 'yearly', 'yhat']
for comp in componentes:
    if comp in forecast_completo.columns:
        print(f"{comp}: Disponible")
```

**Componentes sugeridos:**
- **Gráfico de tendencia**: Línea suavizada de evolución
- **Gráfico de estacionalidad**: Patrón anual típico
- **Separación de componentes**: Trend + Seasonality + Residuals

### 4. Alertas de Anomalías

```python
def detectar_anomalias(valor_real: float, prediccion: float, intervalo: tuple) -> str:
    """Detecta si el valor real está fuera del intervalo esperado."""
    yhat_lower, yhat_upper = intervalo
    
    if valor_real > yhat_upper:
        desviacion = ((valor_real - yhat_upper) / yhat_upper) * 100
        return f"⚠️ ALERTA ALTA: {desviacion:.1f}% por encima del límite superior"
    elif valor_real < yhat_lower:
        desviacion = ((yhat_lower - valor_real) / yhat_lower) * 100
        return f"⚠️ ALERTA BAJA: {desviacion:.1f}% por debajo del límite inferior"
    else:
        return "✅ Dentro del rango esperado"

# Ejemplo de uso
alerta = detectar_anomalias(
    valor_real=2500,
    prediccion=2200,
    intervalo=(2000, 2400)
)
print(alerta)
```

**Componentes sugeridos:**
- **Semáforo**: Verde/Amarillo/Rojo según desviación
- **Notificaciones**: Alertas cuando valores reales difieren significativamente
- **Historial de alertas**: Registro de anomalías detectadas

---

## 🤖 Integración en Chatbot

### 1. Respuestas sobre Forecast

```python
import pandas as pd
import json

# Cargar datos
forecast = pd.read_csv('models/timeserie/regression_timeseries/forecast_futuro.csv')
forecast['ds'] = pd.to_datetime(forecast['ds'])

with open('models/timeserie/regression_timeseries/metadata.json', 'r') as f:
    metadata = json.load(f)

def respuesta_forecast(pregunta: str) -> str:
    """Genera respuestas sobre el forecast de series temporales."""
    pregunta = pregunta.lower()
    
    # Pregunta: predicción general
    if 'predicción' in pregunta or 'pronóstico' in pregunta or 'forecast' in pregunta:
        promedio = forecast['yhat'].mean()
        return f"El modelo predice un promedio de {promedio:.0f} delitos mensuales " + \
               f"para los próximos 12 meses."
    
    # Pregunta: próximo mes
    if 'próximo mes' in pregunta or 'siguiente mes' in pregunta:
        proximo = forecast.iloc[0]
        return f"Para {proximo['ds'].strftime('%B %Y')}, se estiman " + \
               f"{proximo['yhat']:.0f} delitos (rango: {proximo['yhat_lower']:.0f} - {proximo['yhat_upper']:.0f})."
    
    # Pregunta: mes específico
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    for i, mes in enumerate(meses, 1):
        if mes in pregunta:
            fila = forecast[forecast['ds'].dt.month == i]
            if len(fila) > 0:
                f = fila.iloc[0]
                return f"Para {mes.capitalize()}, la predicción es de " + \
                       f"{f['yhat']:.0f} delitos (IC: {f['yhat_lower']:.0f} - {f['yhat_upper']:.0f})."
    
    # Pregunta: tendencia
    if 'tendencia' in pregunta or 'evolución' in pregunta:
        primer_mes = forecast.iloc[0]['yhat']
        ultimo_mes = forecast.iloc[-1]['yhat']
        cambio = ((ultimo_mes - primer_mes) / primer_mes) * 100
        
        if cambio > 5:
            return f"La tendencia es ASCENDENTE. Se espera un aumento de {cambio:.1f}% " + \
                   "en los próximos 12 meses."
        elif cambio < -5:
            return f"La tendencia es DESCENDENTE. Se espera una reducción de {abs(cambio):.1f}% " + \
                   "en los próximos 12 meses."
        else:
            return "La tendencia es ESTABLE. No se esperan cambios significativos."
    
    # Pregunta: mes más alto/bajo
    if 'más alto' in pregunta or 'máximo' in pregunta or 'peor' in pregunta:
        mes_max = forecast.loc[forecast['yhat'].idxmax()]
        return f"El mes con más delitos esperados es {mes_max['ds'].strftime('%B %Y')} " + \
               f"con {mes_max['yhat']:.0f} delitos."
    
    if 'más bajo' in pregunta or 'mínimo' in pregunta or 'mejor' in pregunta:
        mes_min = forecast.loc[forecast['yhat'].idxmin()]
        return f"El mes con menos delitos esperados es {mes_min['ds'].strftime('%B %Y')} " + \
               f"con {mes_min['yhat']:.0f} delitos."
    
    # Pregunta: precisión del modelo
    if 'precisión' in pregunta or 'confiable' in pregunta or 'error' in pregunta:
        mape = metadata['metrics']['MAPE']
        r2 = metadata['metrics']['R2']
        return f"El modelo tiene un error promedio del {mape:.1f}% (MAPE) " + \
               f"y un R² de {r2:.3f}. Esto indica una precisión {'alta' if mape < 10 else 'moderada'}."
    
    return "Puedo responder sobre: predicciones por mes, tendencia general, " + \
           "meses críticos y precisión del modelo."
```

### 2. Ejemplos de Interacción

| Pregunta del Usuario | Respuesta del Chatbot |
|---------------------|----------------------|
| "¿Cuál es la predicción para el próximo mes?" | "Para Enero 2026, se estiman 2,180 delitos (rango: 1,950 - 2,410)." |
| "¿Cuántos delitos habrá en marzo?" | "Para Marzo, la predicción es de 2,350 delitos (IC: 2,120 - 2,580)." |
| "¿Cuál es la tendencia de criminalidad?" | "La tendencia es ASCENDENTE. Se espera un aumento de 4.2% en los próximos 12 meses." |
| "¿Qué mes tendrá más delitos?" | "El mes con más delitos esperados es Octubre 2026 con 2,480 delitos." |
| "¿Qué tan confiable es el modelo?" | "El modelo tiene un error promedio del 7.5% (MAPE) y un R² de 0.82. Esto indica una precisión alta." |
| "Dame el pronóstico para los próximos meses" | "El modelo predice un promedio de 2,215 delitos mensuales para los próximos 12 meses." |

### 3. Generación de Forecast Dinámico

```python
import joblib

def generar_forecast_extendido(meses_adelante: int = 12) -> pd.DataFrame:
    """Genera forecast para un período personalizado."""
    model = joblib.load('models/timeserie/regression_timeseries/prophet_model.joblib')
    
    future = model.make_future_dataframe(periods=meses_adelante, freq='MS')
    forecast = model.predict(future)
    
    # Solo predicciones futuras
    ultima_fecha_entrenamiento = pd.to_datetime(metadata['training_data']['end'])
    forecast_futuro = forecast[forecast['ds'] > ultima_fecha_entrenamiento]
    
    return forecast_futuro[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

# Ejemplo: forecast para 24 meses
forecast_largo = generar_forecast_extendido(24)
print(f"Forecast generado para {len(forecast_largo)} meses")
```

### 4. Respuestas Contextuales

```python
def respuesta_contextual(fecha_actual: str = None) -> str:
    """Genera respuesta contextual basada en la fecha actual."""
    import datetime
    
    if fecha_actual is None:
        hoy = datetime.datetime.now()
    else:
        hoy = pd.to_datetime(fecha_actual)
    
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    # Buscar predicción para el mes actual
    prediccion_actual = forecast[
        (forecast['ds'].dt.month == mes_actual) & 
        (forecast['ds'].dt.year == anio_actual)
    ]
    
    # Buscar predicción para el próximo mes
    mes_siguiente = mes_actual % 12 + 1
    anio_siguiente = anio_actual if mes_siguiente > 1 else anio_actual + 1
    
    prediccion_siguiente = forecast[
        (forecast['ds'].dt.month == mes_siguiente) & 
        (forecast['ds'].dt.year == anio_siguiente)
    ]
    
    respuesta = f"📅 **Contexto Actual ({hoy.strftime('%B %Y')})**\n\n"
    
    if len(prediccion_actual) > 0:
        p = prediccion_actual.iloc[0]
        respuesta += f"- Este mes: ~{p['yhat']:.0f} delitos esperados\n"
    
    if len(prediccion_siguiente) > 0:
        p = prediccion_siguiente.iloc[0]
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        respuesta += f"- {meses[mes_siguiente-1]}: ~{p['yhat']:.0f} delitos esperados\n"
    
    # Tendencia general
    promedio = forecast['yhat'].mean()
    respuesta += f"\n📊 Promedio proyectado (12 meses): {promedio:.0f} delitos/mes"
    
    return respuesta
```

---

## 📊 Componentes del Modelo Prophet

### Estacionalidad Anual

```python
# Obtener componente estacional
model = joblib.load('models/timeserie/regression_timeseries/prophet_model.joblib')

# Crear rango de fechas para un año completo
dates = pd.date_range(start='2025-01-01', periods=12, freq='MS')
df_seasonal = pd.DataFrame({'ds': dates})
forecast_seasonal = model.predict(df_seasonal)

# Patrón estacional
estacionalidad = forecast_seasonal[['ds', 'yearly']].copy()
estacionalidad['mes'] = estacionalidad['ds'].dt.month_name()

print("Patrón estacional anual:")
for _, row in estacionalidad.iterrows():
    signo = "+" if row['yearly'] > 0 else ""
    print(f"  {row['mes']}: {signo}{row['yearly']:.0f}")
```

### Puntos de Cambio (Changepoints)

```python
# Ver puntos de cambio detectados
print(f"Puntos de cambio detectados: {len(model.changepoints)}")
for cp in model.changepoints[-5:]:  # Últimos 5
    print(f"  - {cp.strftime('%Y-%m')}")
```

---

## 🔄 Actualización del Modelo

### Proceso de Re-entrenamiento

1. **Obtener nuevos datos**: Ejecutar pipeline de ETL
2. **Actualizar dataset**: Regenerar `regression_timeseries_dataset.parquet`
3. **Re-entrenar modelo**: Ejecutar notebook `05_eda_regression_timeseries.ipynb`

```python
# Script de actualización automática
def actualizar_forecast():
    """Actualiza el modelo con los datos más recientes."""
    import subprocess
    
    # 1. Actualizar dataset
    subprocess.run(['python', 'scripts/04_generate_regression_timeseries_dataset.py'])
    
    # 2. Re-entrenar (alternativa programática)
    from prophet import Prophet
    import pandas as pd
    import joblib
    
    # Cargar nuevos datos
    df = pd.read_parquet('data/gold/model/regression_timeseries_dataset.parquet')
    df_prophet = df[['fecha', 'total_delitos']].copy()
    df_prophet.columns = ['ds', 'y']
    
    # Entrenar con mejores parámetros
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.1,  # Usar parámetros optimizados
        seasonality_prior_scale=1.0,
        seasonality_mode='additive'
    )
    model.fit(df_prophet)
    
    # Guardar
    joblib.dump(model, 'models/timeserie/regression_timeseries/prophet_model.joblib')
    
    # Generar nuevo forecast
    future = model.make_future_dataframe(periods=12, freq='MS')
    forecast = model.predict(future)
    forecast_futuro = forecast[forecast['ds'] > df_prophet['ds'].max()]
    forecast_futuro[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(
        'models/timeserie/regression_timeseries/forecast_futuro.csv', index=False
    )
    
    print("✅ Modelo actualizado exitosamente")
```

---

## 📝 Notas Importantes

1. **Agregación Departamental**: Este modelo predice a nivel de todo Santander, no por municipio
2. **Frecuencia Mensual**: Las predicciones son mensuales, usar `freq='MS'` para inicio de mes
3. **Intervalo de Confianza**: `yhat_lower` y `yhat_upper` representan el 80% de confianza por defecto
4. **Estacionalidad**: El modelo captura automáticamente patrones anuales
5. **Horizonte de Predicción**: Prophet funciona mejor con horizontes de 6-18 meses

---

## 🎯 Casos de Uso

| Escenario | Uso Recomendado |
|-----------|-----------------|
| "¿Tendencia general de criminalidad?" | Usar forecast completo |
| "¿Cuántos delitos habrá en marzo?" | Consultar `forecast_futuro.csv` |
| "¿Este mes es normal?" | Comparar real vs predicción |
| "Planificación anual de recursos" | Usar forecast 12 meses |
| "Detectar anomalías" | Comparar valores reales vs intervalos |
| "Presentación ejecutiva" | Gráfico de tendencia + pronóstico |

---

## 🔗 Integración con Otros Modelos

El forecast de series temporales complementa los modelos de regresión por municipio:

```python
def resumen_integral():
    """Combina forecast departamental con análisis por municipio."""
    
    # Forecast departamental (series temporales)
    forecast_dept = pd.read_csv('models/timeserie/regression_timeseries/forecast_futuro.csv')
    total_esperado = forecast_dept['yhat'].sum()
    
    # Predicción por municipio (regresión mensual)
    # ... cargar predicciones por municipio ...
    
    respuesta = f"""
    📊 **Resumen Integral de Seguridad**
    
    🏛️ **Nivel Departamental** (Prophet):
    - Próximos 12 meses: {total_esperado:.0f} delitos estimados
    - Promedio mensual: {forecast_dept['yhat'].mean():.0f}
    
    🏘️ **Por Municipios** (XGBoost):
    - Municipio más crítico: [del modelo de regresión]
    - Municipios en alerta: [del modelo de clasificación]
    
    📈 **Tendencia**:
    - General: {'Ascendente' if forecast_dept['yhat'].iloc[-1] > forecast_dept['yhat'].iloc[0] else 'Descendente'}
    """
    return respuesta
```

---

## 📞 Soporte

Para preguntas sobre este modelo:
1. Revisar documentación de Prophet: https://facebook.github.io/prophet/
2. Consultar notebook: `05_eda_regression_timeseries.ipynb`
3. Verificar metadata: `models/timeserie/regression_timeseries/metadata.json`
