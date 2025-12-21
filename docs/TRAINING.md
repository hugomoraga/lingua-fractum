# Guía de Entrenamiento

Guía completa para entrenar modelos personalizados de poesía.

## Índice

1. [Preparación de Datos](#preparación-de-datos)
2. [Entrenamiento Básico](#entrenamiento-básico)
3. [Estrategias de Datasets](#estrategias-de-datasets)
4. [Parámetros Avanzados](#parámetros-avanzados)
5. [Mejores Prácticas](#mejores-prácticas)

## Preparación de Datos

### Formato de Dataset

Los datasets deben estar en formato texto plano (`.txt`) con poemas separados por:

```
=== POEMA ===

[Contenido del poema aquí]

=== POEMA ===

[Otro poema]
```

### Opciones para Obtener Datos

#### Opción 1: Procesar Archivos EPUB

```bash
# Procesar un directorio de EPUBs
poetry run python -m poema_algoritmo.epub_processor data/epub -o data/poems.txt

# Procesar un archivo individual
poetry run python -m poema_algoritmo.epub_processor libro.epub -o data/poems.txt
```

#### Opción 2: Usar el Panel de Administración

1. Accede a `/admin`
2. Ve a la sección "Datasets"
3. Sube un archivo EPUB o agrega poemas manualmente
4. El sistema procesará y guardará el dataset automáticamente

#### Opción 3: Crear Manualmente

Crea un archivo `.txt` con el formato estándar:

```bash
cat > data/mi_dataset.txt << EOF
=== POEMA ===

El amor es un susurro
en la noche silenciosa,
donde las estrellas brillan
y el corazón late fuerte.

=== POEMA ===

La casa abandonada
guarda secretos del pasado,
sus paredes susurran
historias olvidadas.
EOF
```

### Requisitos Mínimos

- **Mínimo**: 50-100 poemas para empezar
- **Recomendado**: 500+ poemas para mejor calidad
- **Ideal**: 1000+ poemas diversos

## Entrenamiento Básico

### Método Rápido (Script Automatizado)

```bash
./scripts/train_poetry_model.sh data/epub data/poems.txt models/poetry_model
```

Este script:
1. Procesa los EPUBs si es necesario
2. Entrena el modelo con parámetros por defecto
3. Guarda el modelo en `models/poetry_model`

### Método Manual

#### Paso 1: Preparar Datos

```bash
# Si tienes EPUBs
poetry run python -m poema_algoritmo.epub_processor data/epub -o data/poems.txt
```

#### Paso 2: Entrenar

```bash
poetry run python -m poema_algoritmo.train_model data/poems.txt \
    -o models/poetry_model \
    -e 5 \
    --batch-size 4 \
    --learning-rate 5e-5
```

#### Paso 3: Usar el Modelo Entrenado

```bash
TRAINED_MODEL_PATH=models/poetry_model poetry run uvicorn poema_algoritmo.main:app --reload
```

### Entrenamiento desde el Panel de Administración

1. Accede a `/admin`
2. Ve a la sección "Entrenamiento"
3. Selecciona el dataset
4. Configura los parámetros:
   - **Épocas**: 5-7 recomendado
   - **Batch size**: 4 (CPU) o 8 (GPU)
   - **Learning rate**: 5e-5
5. Haz clic en "Iniciar Entrenamiento"
6. Monitorea el progreso en tiempo real

## Estrategias de Datasets

### ¿Reentrenar con el Mismo Dataset?

**No recomendado** para múltiples iteraciones:
- Riesgo de overfitting (memorización)
- Pérdida de generalización
- Limitación de estilos

**Solo hazlo si**:
- Es la primera vez entrenando
- Quieres probar un nuevo formato
- Tienes tiempo limitado

### Agregar Nuevos Datasets (Recomendado)

**Ventajas**:
- Mayor diversidad de estilos
- Mejor generalización
- Menos riesgo de overfitting
- Más versatilidad

**Cómo hacerlo**:

```bash
# Combinar múltiples datasets
cat data/poems.txt data/poemas_neruda.txt data/poemas_lorca.txt > data/poems_combined.txt

# Entrenar con el dataset combinado
poetry run python -m poema_algoritmo.train_model data/poems_combined.txt \
    -o models/poetry_model_combined \
    -e 7 \
    --batch-size 4
```

### Fuentes Recomendadas

**Poetas en Español**:
- Pablo Neruda
- Federico García Lorca
- Antonio Machado
- Octavio Paz
- Gabriela Mistral
- Rubén Darío

**Dónde encontrar**:
- [Project Gutenberg](https://www.gutenberg.org/)
- [Biblioteca Digital Hispánica](http://www.bne.es/)
- [Cervantes Virtual](https://www.cervantesvirtual.com/)
- [Wikisource](https://es.wikisource.org/)

## Parámetros Avanzados

### Parámetros de Entrenamiento

| Parámetro | Descripción | Default | Recomendado |
|-----------|-------------|---------|-------------|
| `-e, --epochs` | Número de épocas | 3 | 5-7 |
| `--batch-size` | Tamaño del batch | 4 | 4 (CPU), 8 (GPU) |
| `--learning-rate` | Tasa de aprendizaje | 5e-5 | 5e-5 |
| `--max-length` | Longitud máxima | 512 | 512 |
| `-b, --base-model` | Modelo base | gpt2 | gpt2 o DeepESP/gpt2-spanish |

### Ejemplo con Parámetros Personalizados

```bash
poetry run python -m poema_algoritmo.train_model data/poems.txt \
    -o models/poetry_model_custom \
    -e 10 \
    --batch-size 8 \
    --learning-rate 3e-5 \
    --max-length 256 \
    -b DeepESP/gpt2-spanish
```

### Entrenamiento Incremental

Puedes entrenar en fases:

```bash
# Fase 1: Entrenamiento base
poetry run python -m poema_algoritmo.train_model data/poems.txt \
    -o models/poetry_base \
    -e 5

# Fase 2: Fine-tuning con más datos
poetry run python -m poema_algoritmo.train_model data/poems_combined.txt \
    -o models/poetry_enhanced \
    -b models/poetry_base \
    -e 3
```

## Mejores Prácticas

### 1. Diversidad de Datos

✅ **Hacer**:
- Diferentes poetas
- Diferentes épocas
- Diferentes temas
- Diferentes estilos (soneto, verso libre, etc.)

❌ **Evitar**:
- Solo un poeta
- Solo un estilo
- Solo un tema

### 2. Calidad sobre Cantidad

✅ **Hacer**:
- Limpiar metadatos
- Verificar calidad de poemas
- Eliminar texto basura

❌ **Evitar**:
- Poemas incompletos
- Texto que no es poesía
- Metadatos sin limpiar

### 3. Balance

✅ **Hacer**:
- Mezclar estilos y épocas
- Incluir diferentes longitudes
- Balancear temas

❌ **Evitar**:
- Sobreespecialización
- Desbalance extremo

### 4. Validación

✅ **Hacer**:
- Separar 10-20% para validación
- Probar con diferentes prompts
- Verificar que no esté sobreentrenado

### 5. Tiempos de Entrenamiento

| Hardware | 100 poemas | 500 poemas | 1000 poemas |
|----------|------------|------------|-------------|
| CPU | 2-4 horas | 10-20 horas | 20-40 horas |
| GPU | 30-60 min | 2-4 horas | 4-8 horas |

## Formato de Instrucciones

El sistema entrena automáticamente con formato de instrucciones para que el modelo aprenda a seguir directrices:

**Formato generado automáticamente**:
```
Tema: casa

Poema sobre casa:

[poema]
```

O variantes como:
```
Escribe un poema sobre casa:

[poema]
```

Esto permite que el modelo entienda directrices como:
- `"casa"`
- `"escribe un poema triste sobre la casa"`
- `"soneto sobre el amor"`

## Solución de Problemas

### El modelo no sigue las instrucciones

- **Aumenta las épocas**: Prueba con 7-10 épocas
- **Verifica los datos**: Asegúrate de tener suficientes poemas
- **Reentrena**: Puede necesitar más entrenamiento

### El modelo genera texto sin sentido

- **Reduce la temperatura**: Usa 0.5-0.7 en lugar de 0.9
- **Revisa los datos**: Puede haber poemas de mala calidad
- **Reduce las épocas**: Puede estar sobreentrenado

### El entrenamiento es muy lento

- **Usa GPU**: Mucho más rápido
- **Reduce batch_size**: Si tienes poca memoria
- **Reduce max_length**: Secuencias más cortas = más rápido

### Overfitting

- **Agrega más datos**: Más diversidad
- **Reduce épocas**: Menos iteraciones
- **Aumenta learning rate**: Aprendizaje más rápido pero cuidado

## Verificación Post-Entrenamiento

Después de entrenar, verifica que el modelo funciona:

```bash
# Verificar que el modelo existe
ls -lh models/poetry_model/

# Deberías ver:
# - config.json
# - model.safetensors
# - tokenizer_config.json
# - vocab.json
```

Probar con diferentes directrices:
- `"casa"`
- `"poema triste sobre la noche"`
- `"soneto sobre el amor"`

