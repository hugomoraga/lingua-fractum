# 🚀 Guía Rápida: Entrenar Modelo con EPUBs

## Pasos Rápidos

### 1. Instalar dependencias
```bash
poetry install
```

### 2. Preparar tus archivos EPUB
```bash
mkdir -p data/epub
# Copia tus archivos .epub aquí
cp /ruta/a/tus/poemas.epub data/epub/
```

### 3. Entrenar (todo en uno)
```bash
./scripts/train_poetry_model.sh data/epub data/poems.txt models/poetry_model
```

### 4. Usar tu modelo entrenado
```bash
TRAINED_MODEL_PATH=models/poetry_model poetry run uvicorn poema_algoritmo.main:app --reload
```

Luego abre: http://localhost:8000

## Pasos Manuales (si prefieres más control)

### Paso 1: Extraer poesías
```bash
poetry run python -m poema_algoritmo.epub_processor data/epub -o data/poems.txt
```

### Paso 2: Entrenar
```bash
poetry run python -m poema_algoritmo.train_model data/poems.txt \
    -o models/poetry_model \
    -e 5 \
    --batch-size 4
```

### Paso 3: Usar
```bash
TRAINED_MODEL_PATH=models/poetry_model poetry run uvicorn poema_algoritmo.main:app --reload
```

## Notas Importantes

- **Mínimo de poesías**: 50-100 para empezar, 500+ para mejor calidad
- **Tiempo de entrenamiento**: 
  - CPU: ~2-4 horas para 100 poesías
  - GPU: ~30-60 minutos para 100 poesías
- **Espacio necesario**: ~2-5GB para el modelo entrenado
- **El modelo entrenado tiene prioridad**: Si existe, se usa automáticamente

## Verificar que funciona

Después de entrenar, verifica que el modelo se creó:
```bash
ls -lh models/poetry_model/
```

Deberías ver archivos como:
- `config.json`
- `pytorch_model.bin` o `model.safetensors`
- `tokenizer_config.json`
- `vocab.json`

