# Plataforma de Poesía

Sistema de generación de poesía mediante inteligencia artificial con interfaz web moderna y panel de administración completo.

## Características

- **Generación de poesía**: Modelos de lenguaje entrenados para generar poemas en español
- **Interfaz web**: Diseño minimalista y geométrico con estética oscura
- **Panel de administración**: Gestión completa de datasets, entrenamiento y modelos
- **Procesamiento EPUB**: Conversión automática de libros EPUB a datasets de entrenamiento
- **Integración LM Studio**: Soporte opcional para modelos locales avanzados
- **API REST**: Endpoints para integración programática

## Requisitos

- Python 3.11+
- Poetry (gestor de dependencias)
- 8GB+ RAM (16GB recomendado para entrenamiento)
- GPU opcional pero recomendada para entrenamiento

## Instalación

```bash
# Clonar el repositorio
git clone <repo-url>
cd lingua-fractum

# Instalar dependencias
poetry install

# Activar entorno virtual
poetry shell
```

## Inicio Rápido

### 1. Iniciar el servidor

```bash
poetry run uvicorn poema_algoritmo.main:app --reload
```

### 2. Acceder a la plataforma

- **Interfaz principal**: http://localhost:8000
- **Panel de administración**: http://localhost:8000/admin

### 3. Generar tu primer poema

En la interfaz web, escribe una directriz como:
- `"casa"`
- `"escribe un poema triste sobre la noche"`
- `"soneto sobre el amor"`

## Estructura del Proyecto

```
lingua-fractum/
├── src/poema_algoritmo/      # Código fuente principal
│   ├── main.py               # Aplicación FastAPI
│   ├── poem_generator.py     # Generador de poemas
│   ├── poetry_agent.py       # Agente de poesía
│   ├── train_model.py        # Entrenamiento de modelos
│   ├── epub_processor.py    # Procesador EPUB
│   ├── admin.py              # Panel de administración
│   └── static/               # Archivos estáticos
├── data/                     # Datasets y archivos EPUB
├── models/                   # Modelos entrenados
├── docs/                     # Documentación
└── scripts/                  # Scripts de utilidad
```

## Documentación

- **[Inicio Rápido](docs/GETTING_STARTED.md)**: Guía de primeros pasos
- **[Entrenamiento](docs/TRAINING.md)**: Guía completa de entrenamiento de modelos
- **[Panel de Administración](docs/ADMIN_PANEL.md)**: Documentación del panel admin
- **[API](docs/API.md)**: Referencia de endpoints API
- **[LM Studio](docs/LM_STUDIO.md)**: Integración con LM Studio
- **[Ejemplos](docs/EXAMPLES.md)**: Ejemplos de uso

## Uso Básico

### Generar un poema

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "casa",
    "max_sentences": 8,
    "temperature": 0.7
  }'
```

### Panel de Administración

El panel de administración (`/admin`) permite:
- Gestionar datasets (crear, editar, eliminar poemas)
- Subir archivos EPUB y convertirlos a datasets
- Entrenar modelos personalizados
- Gestionar modelos entrenados
- Ver estadísticas del sistema

## Modelos

El sistema soporta múltiples fuentes de modelos:

1. **Modelo entrenado localmente** (prioridad): `models/poetry_model/`
2. **LM Studio** (si está disponible): Modelos locales avanzados
3. **Modelo base**: GPT-2 español o GPT-2 base como fallback

## Desarrollo

```bash
# Modo desarrollo con recarga automática
poetry run uvicorn poema_algoritmo.main:app --reload --host 0.0.0.0 --port 8000

# Ejecutar tests
poetry run pytest tests/
```

## Licencia

Este proyecto es de código abierto.

## Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Crea un issue para discutir cambios mayores
2. Haz fork del repositorio
3. Crea una rama para tu feature
4. Envía un pull request
