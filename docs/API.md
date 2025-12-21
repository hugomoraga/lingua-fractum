# Referencia de API

Documentación completa de los endpoints de la API REST.

## Base URL

```
http://localhost:8000
```

## Endpoints Principales

### Generación de Poemas

#### `POST /api/generate`

Genera un poema basado en una directriz.

**Request Body**:
```json
{
  "input_text": "string (requerido)",
  "max_sentences": 8 (opcional, default: 8),
  "temperature": 0.7 (opcional, default: 0.7)
}
```

**Response**:
```json
{
  "poem": "texto del poema generado",
  "directive": "directriz extraída",
  "success": true
}
```

**Ejemplo**:
```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "casa",
    "max_sentences": 8,
    "temperature": 0.7
  }'
```

### Estado del Sistema

#### `GET /api/health`

Verifica el estado del servidor.

**Response**:
```json
{
  "status": "ok"
}
```

#### `GET /api/lm-studio-status`

Verifica el estado de LM Studio.

**Response**:
```json
{
  "available": true,
  "using_lm_studio": true,
  "message": "LM Studio disponible"
}
```

## Endpoints de Administración

### Datasets

#### `GET /admin/api/datasets`

Lista todos los datasets disponibles.

**Response**:
```json
[
  {
    "name": "poems.txt",
    "path": "data/poems.txt",
    "size": 12345,
    "poems_count": 845,
    "created": "2024-01-01T00:00:00"
  }
]
```

#### `POST /admin/api/datasets`

Crea un nuevo dataset.

**Request Body** (form-data):
```
poem: string (contenido del poema)
filename: string (nombre del archivo)
```

#### `GET /admin/api/datasets/{filename}/poems`

Obtiene los poemas de un dataset con paginación.

**Query Parameters**:
- `page`: Número de página (default: 1)
- `per_page`: Poemas por página (default: 50)

**Response**:
```json
{
  "poems": [
    {
      "id": 0,
      "text": "contenido del poema",
      "length": 123
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 845,
    "total_pages": 17
  }
}
```

#### `GET /admin/api/datasets/{filename}/poems/{poem_id}`

Obtiene un poema específico por ID.

**Response**:
```json
{
  "id": 0,
  "text": "contenido del poema",
  "length": 123
}
```

#### `PUT /admin/api/datasets/{filename}/poems/{poem_id}`

Actualiza un poema.

**Request Body**:
```json
{
  "text": "nuevo contenido del poema"
}
```

#### `DELETE /admin/api/datasets/{filename}/poems/{poem_id}`

Elimina un poema individual.

**Response**:
```json
{
  "success": true,
  "message": "Poema eliminado"
}
```

#### `DELETE /admin/api/datasets/{filename}/poems/batch-delete`

Elimina múltiples poemas.

**Request Body**:
```json
{
  "poem_ids": [0, 1, 2]
}
```

**Response**:
```json
{
  "success": true,
  "message": "3 poema(s) eliminado(s)",
  "deleted_count": 3
}
```

#### `DELETE /admin/api/datasets/{filename}`

Elimina un dataset completo.

**Response**:
```json
{
  "success": true,
  "message": "Dataset eliminado"
}
```

#### `PUT /admin/api/datasets/{filename}/rename`

Renombra un dataset.

**Request Body**:
```json
{
  "new_name": "nuevo_nombre.txt"
}
```

### Entrenamiento

#### `POST /admin/api/training/start`

Inicia un proceso de entrenamiento.

**Request Body**:
```json
{
  "poems_file": "data/poems.txt",
  "output_dir": "models/poetry_model",
  "epochs": 5,
  "batch_size": 4,
  "learning_rate": 5e-5,
  "base_model": null
}
```

**Response**:
```json
{
  "success": true,
  "message": "Entrenamiento iniciado",
  "training_id": "unique-id"
}
```

#### `GET /admin/api/training/status`

Obtiene el estado del entrenamiento actual.

**Response**:
```json
{
  "status": "training",
  "progress": 45.5,
  "current_epoch": 2,
  "total_epochs": 5,
  "loss": 2.34,
  "elapsed_time": 3600
}
```

**Estados posibles**:
- `idle`: Sin entrenamiento activo
- `training`: Entrenando actualmente
- `completed`: Completado
- `error`: Error en el entrenamiento

#### `POST /admin/api/training/cancel`

Cancela el entrenamiento actual.

**Response**:
```json
{
  "success": true,
  "message": "Entrenamiento cancelado"
}
```

### Modelos

#### `GET /admin/api/models`

Lista todos los modelos disponibles.

**Response**:
```json
[
  {
    "name": "poetry_model",
    "path": "models/poetry_model",
    "size": 524288000,
    "created": "2024-01-01T00:00:00"
  }
]
```

#### `DELETE /admin/api/models/{model_name}`

Elimina un modelo.

**Response**:
```json
{
  "success": true,
  "message": "Modelo eliminado"
}
```

### Estadísticas

#### `GET /admin/api/stats`

Obtiene estadísticas del sistema.

**Response**:
```json
{
  "datasets": {
    "count": 5,
    "total_size": 1234567
  },
  "models": {
    "count": 2,
    "total_size": 1048576000
  },
  "epub_files": {
    "count": 3,
    "total_size": 5678901
  }
}
```

### Procesamiento EPUB

#### `POST /admin/api/datasets/upload-epub`

Sube y procesa un archivo EPUB.

**Request** (multipart/form-data):
- `file`: Archivo EPUB
- `dataset_name`: Nombre del dataset (opcional)

**Response**:
```json
{
  "success": true,
  "message": "EPUB procesado correctamente",
  "dataset_name": "nombre_dataset.txt",
  "poems_extracted": 150
}
```

## Códigos de Estado HTTP

- `200 OK`: Solicitud exitosa
- `201 Created`: Recurso creado exitosamente
- `400 Bad Request`: Solicitud inválida
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

## Manejo de Errores

Las respuestas de error siguen este formato:

```json
{
  "detail": "Mensaje de error descriptivo"
}
```

**Ejemplos**:

```json
{
  "detail": "Dataset no encontrado"
}
```

```json
{
  "detail": "Error al procesar EPUB: formato inválido"
}
```

## Autenticación

Actualmente la API no requiere autenticación. En producción, se recomienda implementar:

- Tokens de API
- Autenticación basada en sesión
- OAuth2

## Límites

- **Paginación**: Máximo 100 poemas por página
- **Tamaño de archivo**: Máximo 50MB para uploads
- **Tiempo de entrenamiento**: Sin límite, pero se recomienda monitorear

## Ejemplos de Uso

### Generar un Poema

```python
import requests

response = requests.post(
    "http://localhost:8000/api/generate",
    json={
        "input_text": "casa",
        "max_sentences": 8,
        "temperature": 0.7
    }
)

data = response.json()
print(data["poem"])
```

### Listar Datasets

```python
import requests

response = requests.get("http://localhost:8000/admin/api/datasets")
datasets = response.json()

for dataset in datasets:
    print(f"{dataset['name']}: {dataset['poems_count']} poemas")
```

### Agregar un Poema

```python
import requests

response = requests.post(
    "http://localhost:8000/admin/api/datasets",
    data={
        "poem": "Contenido del poema aquí",
        "filename": "mi_dataset.txt"
    }
)

print(response.json())
```

### Iniciar Entrenamiento

```python
import requests

response = requests.post(
    "http://localhost:8000/admin/api/training/start",
    json={
        "poems_file": "data/poems.txt",
        "output_dir": "models/poetry_model",
        "epochs": 5,
        "batch_size": 4,
        "learning_rate": 5e-5
    }
)

print(response.json())
```

