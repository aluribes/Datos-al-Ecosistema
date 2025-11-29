# 00 - Setup: Estructura de Carpetas

## Descripción

El script `00_setup.py` inicializa la estructura de carpetas del proyecto siguiendo la arquitectura Medallion (Bronze → Silver → Gold). Debe ejecutarse antes de cualquier otro script del pipeline.

## Script

| Archivo | Descripción |
|---------|-------------|
| `scripts/00_setup.py` | Crea la estructura de directorios para el proyecto |

## Ejecución

```bash
python scripts/00_setup.py
```

## Estructura de Carpetas Creada

```
data/
├── bronze/                    # Datos crudos (sin procesar)
│   ├── socrata_api/           # JSONs de la API Socrata de Bucaramanga
│   ├── policia_scraping/      # Excels descargados de Policía Nacional
│   ├── dane_geo/              # Datos geográficos DANE (DIVIPOLA, GeoJSON)
│   ├── poblacion_dane/        # Datos de población DANE (ZIPs)
│   └── metas/                 # Datos de metas departamentales
│
├── silver/                    # Datos limpios (procesados)
│   ├── socrata_api/           # Parquets procesados de Socrata
│   ├── policia_scraping/      # Parquets procesados de Policía
│   ├── dane_geo/              # Parquets geográficos procesados
│   ├── poblacion/             # Parquet de población Santander
│   ├── delitos/               # Consolidado de delitos
│   └── metas/                 # Parquets de metas procesadas
│
└── gold/                      # Datos integrados (listos para análisis)
    ├── base/                  # Parquets gold individuales
    ├── analytics/             # Datos analíticos agregados
    ├── model/                 # Datasets para modelos ML
    └── dashboard/             # Datos para dashboard
```

## Arquitectura Medallion

| Capa | Propósito | Formato Típico |
|------|-----------|----------------|
| **Bronze** | Datos crudos tal como se obtienen de las fuentes | JSON, Excel, CSV, GeoJSON |
| **Silver** | Datos limpios, tipados y normalizados | Parquet |
| **Gold** | Datos integrados, agregados y listos para consumo | Parquet |

## Notas

- El script es idempotente: puede ejecutarse múltiples veces sin efectos secundarios
- Las carpetas se crean con `mkdir -p` (crea padres si no existen)
- No elimina archivos existentes en las carpetas

## Siguiente Paso

Después de crear la estructura, proceder con los scripts de la capa Bronze:
- Ver [01_bronze.md](01_bronze.md) para la extracción de datos
