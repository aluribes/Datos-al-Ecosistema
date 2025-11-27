# Prácticas de Desarrollo

Guía de convenciones y buenas prácticas para contribuir al proyecto.

## Estructura del proyecto

```
Datos-al-Ecosistema/
├── data/                 # Datos (no modificar manualmente)
│   ├── bronze/          # Datos crudos
│   ├── silver/          # Datos limpios
│   └── gold/            # Datos integrados
│       ├── base/        # Datasets base limpios
│       ├── analytics/   # Dataset analítico enriquecido
│       └── model/       # Datasets preparados para ML
├── models/              # Modelos entrenados
│   ├── *.joblib         # Modelos serializados
│   ├── *_features.json  # Features requeridas
│   └── *_metadata.json  # Métricas y configuración
├── scripts/             # Pipeline de procesamiento
├── utils/               # Utilidades compartidas
├── docs/                # Documentación
└── app.py               # Aplicación principal
```

---

## Convenciones de código

### Idioma

- **Código**: Inglés (nombres de variables, funciones)
- **Comentarios**: Español
- **Documentación**: Español

```python
# ✅ Correcto
def load_silver() -> pd.DataFrame:
    """Carga los datos de la capa Silver."""
    ...

# ❌ Evitar
def cargar_silver() -> pd.DataFrame:
    """Loads silver layer data."""
    ...
```

### Nombrado de archivos

Los scripts siguen el patrón `NN_descripcion.py`:

| Prefijo | Capa | Ejemplo |
|---------|------|---------|
| `00_` | Setup | `00_setup.py` |
| `01_` | Bronze | `01_extract_bronze.py` |
| `02_` | Silver | `02_process_policia.py` |
| `03_` | Gold | `03_generate_gold.py` |
| `04_` | Model/Analytics | `04_generate_analytics.py` |
| `05_` | ML Training | `05_train_crime_rate_model.py` |

---

## Estructura de scripts

Cada script debe seguir esta estructura:

```python
"""
NN_nombre_script.py
====================

Descripción breve del script.

Entrada:
    data/silver/archivo_entrada.parquet

Salida:
    data/gold/archivo_salida.parquet
"""

from pathlib import Path

import pandas as pd

# === CONFIGURACIÓN ===
# Subimos un nivel desde scripts/ para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Rutas de entrada
INPUT_FILE = DATA_DIR / "silver" / "archivo.parquet"

# Rutas de salida
OUTPUT_FILE = DATA_DIR / "gold" / "resultado.parquet"


def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)


def load_data() -> pd.DataFrame:
    """Carga los datos de entrada."""
    ...


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Procesa los datos."""
    ...


def main() -> None:
    """Función principal del script."""
    print("=" * 60)
    print("NOMBRE DEL PROCESO")
    print("=" * 60)
    
    df = load_data()
    df = process_data(df)
    
    ensure_folder(OUTPUT_FILE.parent)
    df.to_parquet(OUTPUT_FILE, index=False)
    
    print(f"✔ Archivo generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
```

### Secciones obligatorias

1. **Docstring de módulo**: Descripción, entrada y salida
2. **Imports**: Ordenados (stdlib, terceros, locales)
3. **Configuración**: Constantes y rutas al inicio
4. **Funciones utilitarias**: `ensure_folder()` para crear directorios
5. **Funciones de negocio**: Lógica modularizada
6. **Main**: Punto de entrada con `if __name__ == "__main__"`

### Docstring de módulo

Todos los scripts deben tener un docstring al inicio con:

```python
"""
NN_nombre_script.py
====================

Descripción de lo que hace el script.

Entrada:
    ruta/al/archivo/entrada.parquet

Salida:
    ruta/al/archivo/salida.parquet

Notas adicionales (opcional):
    - Detalles de implementación
    - Uso desde línea de comandos
"""
```

### Función `ensure_folder`

Usar esta función estándar para crear directorios:

```python
def ensure_folder(path: Path) -> None:
    """Crea directorio si no existe."""
    path.mkdir(parents=True, exist_ok=True)
```

### Separadores visuales

Para scripts largos, usar separadores de 60 caracteres:

```python
print("=" * 60)
print("NOMBRE DEL PROCESO")
print("=" * 60)
```

---

## Manejo de rutas

### ✅ Usar `pathlib`

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "silver"
OUTPUT_FILE = DATA_DIR / "resultado.parquet"
```

### ❌ Evitar `os.path`

```python
import os

# No recomendado
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "silver")
```

### ❌ Evitar rutas relativas sin ancla

```python
# No recomendado - depende del directorio de ejecución
DATA_DIR = Path("data/silver")
```

---

## Type hints

Todas las funciones deben incluir type hints:

```python
def load_data(path: Path) -> pd.DataFrame:
    """Carga un archivo parquet."""
    return pd.read_parquet(path)


def process_names(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Normaliza nombres en las columnas especificadas."""
    ...


def save_output(df: pd.DataFrame | gpd.GeoDataFrame, path: Path) -> None:
    """Guarda el DataFrame en formato parquet."""
    df.to_parquet(path, index=False)
```

### Tipos comunes

| Tipo | Uso |
|------|-----|
| `pd.DataFrame` | DataFrames de pandas |
| `gpd.GeoDataFrame` | DataFrames con geometría |
| `Path` | Rutas de archivos |
| `list[str]` | Lista de strings |
| `dict[str, int]` | Diccionario |
| `int \| None` | Valor opcional |
| `-> None` | Función sin retorno |

---

## Formato de datos

### Entrada/Salida

| Capa | Formato entrada | Formato salida |
|------|-----------------|----------------|
| Bronze | JSON, Excel, GeoJSON | (mismo) |
| Silver | Bronze formats | Parquet |
| Gold | Parquet | Parquet |

### ¿Por qué Parquet?

- Compresión eficiente
- Preserva tipos de datos
- Lectura rápida con pandas/geopandas
- Compatible con herramientas de Big Data

---

## Logging y mensajes

Usar `print()` para indicar estado:

```python
print("✔ Archivo cargado correctamente")
print("➤ Procesando datos...")
print("⚠️ Advertencia: archivo no encontrado")
print("❌ Error: no se pudo procesar")
```

---

## Validaciones

Siempre verificar que los archivos de entrada existen:

```python
def check_exists(path: Path, label: str | None = None) -> None:
    """Verifica que un archivo exista antes de procesarlo."""
    if not path.exists():
        msg = f"ERROR: No se encontró el archivo requerido:\n{path}"
        if label:
            msg += f"\n(dataset: {label})"
        print(msg)
        sys.exit(1)
    else:
        print(f"✔ Archivo encontrado: {path}")
```

---

## Git

### Flujo de trabajo

Todos los cambios se realizan mediante **branches** y **Pull Requests (PRs)**:

1. Crear una branch desde `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/nueva-funcionalidad
   ```

2. Realizar los cambios y commits

3. Subir la branch:
   ```bash
   git push origin feature/nueva-funcionalidad
   ```

4. Crear un **Pull Request** en GitHub

5. Esperar revisión y aprobación

6. Hacer **merge** a `main`

### Branches

| Patrón | Uso |
|--------|-----|
| `main` | Producción estable |
| `nombre_usuario/nombre` | Nueva funcionalidad |
| `nombre_usuario/f/nombre` | Corrección de errores |

---


## Dependencias

Al agregar una nueva librería:

1. Instalar con `pip install nombre`
2. Agregar a `requirements.txt` con versión exacta:
   ```
   nueva_libreria==1.2.3
   ```
3. Documentar su uso en el script correspondiente
