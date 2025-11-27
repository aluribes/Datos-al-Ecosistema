# Instalación

Guía para configurar el entorno de desarrollo del proyecto.

## Requisitos previos

- Python 3.12 o superior
- `pip` (incluido con Python)
- `git` para clonar el repositorio

## Pasos de instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/aluribes/Datos-al-Ecosistema.git
cd Datos-al-Ecosistema
```

### 2. Crear entorno virtual

Se recomienda usar un entorno virtual para aislar las dependencias del proyecto.

```bash
python3 -m venv .venv
```

Activar el entorno:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

> 💡 Sabrás que el entorno está activo cuando veas `(venv)` al inicio de tu terminal.

### 3. Instalar dependencias

```bash
# Linux / macOS
source setup.sh

# Windows
setup
```

## Estructura del proyecto

Una vez instalado, la estructura principal es:

```
Datos-al-Ecosistema/
├── data/                 # Datos (bronze, silver, gold)
├── scripts/              # Pipeline de procesamiento
├── utils/                # Utilidades compartidas
├── docs/                 # Documentación
├── requirements.txt      # Dependencias
├── setup.bat             # Configuración en Windows
├── setup.sh              # Configuración en Linux o MacOS
└── app.py                # Aplicación principal

```

## Siguiente paso

Consulta la documentación del pipeline en [`docs/pipeline/`](pipeline/) para entender cómo ejecutar los scripts de procesamiento.
