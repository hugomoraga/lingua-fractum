# Plataforma de Poesía

Una plataforma web moderna para generar poemas usando inteligencia artificial. Escribe un tema o idea y obtén poemas únicos generados automáticamente.

## 🚀 Características

- ✨ Interfaz web moderna y responsive
- 🎨 Diseño elegante con gradientes y animaciones
- 🤖 Generación de poemas usando modelos de lenguaje (GPT-2)
- ⚙️ Controles ajustables (longitud, creatividad)
- 📋 Copiar poemas generados fácilmente
- 🌐 API REST para integraciones

## 📋 Requisitos

- Python 3.11 o superior
- Poetry (gestor de dependencias)

## 🔧 Instalación

1. Instala las dependencias usando Poetry:

```bash
poetry install
```

2. Activa el entorno virtual:

```bash
poetry shell
```

## 🎯 Uso

### Iniciar el servidor

```bash
poetry run uvicorn poema_algoritmo.main:app --reload
```

O desde el código:

```bash
poetry run python -m poema_algoritmo.main
```

### Acceder a la plataforma

Abre tu navegador y ve a: `http://localhost:8000`

### Usar la API

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "el amor",
    "max_length": 200,
    "temperature": 0.9
  }'
```

## 🎨 Características de la Interfaz

- **Input de texto**: Escribe el tema sobre el que quieres el poema
- **Control de longitud**: Ajusta la longitud máxima del poema (100-500 caracteres)
- **Control de creatividad**: Ajusta la temperatura (0.5-1.5) para más o menos creatividad
- **Generación**: Haz clic en "Generar Poema" o usa Ctrl+Enter
- **Copiar**: Copia el poema generado al portapapeles
- **Nuevo poema**: Limpia y empieza de nuevo

## 🏗️ Estructura del Proyecto

```
poema-algoritmo/
├── src/
│   └── poema_algoritmo/
│       ├── __init__.py
│       ├── main.py              # Aplicación FastAPI
│       ├── poem_generator.py    # Generador de poemas
│       └── static/              # Archivos estáticos
│           ├── index.html
│           ├── style.css
│           └── script.js
├── tests/
├── pyproject.toml
└── README.md
```

## 🔌 API Endpoints

### `GET /`
Página principal de la plataforma

### `POST /api/generate`
Genera un poema basado en el input

**Body:**
```json
{
  "input_text": "string (requerido)",
  "max_length": 200 (opcional),
  "temperature": 0.9 (opcional)
}
```

**Response:**
```json
{
  "poem": "texto del poema generado",
  "success": true
}
```

### `GET /api/health`
Verifica el estado del servidor

## 🧠 Modelo de IA

La plataforma utiliza modelos de lenguaje pre-entrenados de Hugging Face:
- Intenta cargar modelos específicos para español
- Si no están disponibles, usa GPT-2 base
- Incluye un sistema de fallback con plantillas de poemas

### 📦 Almacenamiento de Modelos

**Sí, los modelos se guardan localmente:**
- Los modelos se descargan y guardan en: `~/.cache/huggingface/transformers/`
- Tamaño aproximado: ~500 MB para GPT-2 base
- Una vez descargados, funcionan sin conexión a internet

### 🔧 Modos de Operación

**Modo normal (con descarga automática):**
```bash
poetry run uvicorn poema_algoritmo.main:app --reload
```
- Primera vez: descarga el modelo (requiere internet)
- Siguientes veces: usa el modelo en caché local

**Modo solo-local (sin descarga):**
```bash
USE_LOCAL_MODELS_ONLY=true poetry run uvicorn poema_algoritmo.main:app --reload
```
- Solo usa modelos ya descargados en caché
- Si no hay modelos locales, usa el fallback con plantillas
- No requiere conexión a internet

## 📝 Notas

- La primera vez que se ejecuta, el modelo se descarga automáticamente (puede tardar unos minutos y requiere ~500 MB de espacio)
- El modelo se carga en memoria (~500 MB RAM), por lo que el primer poema puede tardar más
- Una vez descargado, funciona completamente offline
- Si no hay modelo disponible, usa generación con plantillas (sin IA)

## 🎓 Entrenar tu Propio Modelo

Puedes entrenar un modelo personalizado con tus propias poesías en español desde archivos EPUB.

### Proceso Completo

**1. Preparar tus archivos EPUB:**
```bash
# Coloca tus archivos .epub en un directorio
mkdir -p data/epub
# Copia tus archivos EPUB ahí
cp tus_poemas.epub data/epub/
```

**2. Extraer poesías de EPUBs:**
```bash
# Desde un directorio
poetry run python -m poema_algoritmo.epub_processor data/epub -o data/poems.txt

# O desde un archivo individual
poetry run python -m poema_algoritmo.epub_processor libro.epub -o data/poems.txt
```

**3. Entrenar el modelo:**
```bash
poetry run python -m poema_algoritmo.train_model data/poems.txt \
    -o models/poetry_model \
    -e 5 \
    --batch-size 4 \
    --learning-rate 5e-5
```

**O usar el script automatizado:**
```bash
./scripts/train_poetry_model.sh data/epub data/poems.txt models/poetry_model
```

**4. Usar tu modelo entrenado:**
```bash
TRAINED_MODEL_PATH=models/poetry_model poetry run uvicorn poema_algoritmo.main:app --reload
```

### Parámetros de Entrenamiento

- `-e, --epochs`: Número de épocas (default: 3, recomendado: 3-10)
- `--batch-size`: Tamaño del batch (default: 4, aumentar si tienes GPU)
- `--learning-rate`: Tasa de aprendizaje (default: 5e-5)
- `--max-length`: Longitud máxima de secuencia (default: 512)
- `-b, --base-model`: Modelo base (default: gpt2, puedes usar "gpt2-medium" para mejor calidad)

### Requisitos para Entrenamiento

- **Mínimo recomendado**: 50-100 poesías
- **Ideal**: 500+ poesías para mejor calidad
- **GPU recomendada**: El entrenamiento es mucho más rápido con GPU
- **RAM**: Al menos 8GB (16GB+ recomendado)
- **Espacio en disco**: ~2-5GB para el modelo entrenado

### Estructura de Datos

```
poema-algoritmo/
├── data/
│   ├── epub/          # Archivos EPUB con poesías
│   └── poems.txt      # Poesías extraídas (formato texto)
├── models/
│   └── poetry_model/  # Modelo entrenado (se crea después del entrenamiento)
└── scripts/
    └── train_poetry_model.sh
```

## 🛠️ Desarrollo

Para desarrollo con recarga automática:

```bash
poetry run uvicorn poema_algoritmo.main:app --reload --host 0.0.0.0 --port 8000
```

## 📄 Licencia

Este proyecto es de código abierto.

