# Guía de Inicio Rápido

Esta guía te ayudará a poner en marcha la Plataforma de Poesía en minutos.

## Instalación

### 1. Requisitos Previos

- Python 3.11 o superior
- Poetry instalado ([instrucciones](https://python-poetry.org/docs/#installation))
- 8GB+ de RAM

### 2. Instalar Dependencias

```bash
poetry install
```

### 3. Activar Entorno Virtual

```bash
poetry shell
```

## Primeros Pasos

### Iniciar el Servidor

```bash
poetry run uvicorn poema_algoritmo.main:app --reload
```

El servidor estará disponible en: http://localhost:8000

### Interfaz Web

1. Abre tu navegador en `http://localhost:8000`
2. Escribe una directriz en el campo de texto (ej: `"casa"` o `"poema sobre el amor"`)
3. Ajusta los controles:
   - **Frases**: Número de frases objetivo (3-20)
   - **Temperatura**: Creatividad (0.5-1.5)
4. Haz clic en "Generar"
5. Copia o descarga el poema generado

### Panel de Administración

Accede al panel en: `http://localhost:8000/admin`

El panel permite:
- Ver y gestionar datasets
- Agregar poemas manualmente
- Subir archivos EPUB y convertirlos
- Entrenar modelos personalizados
- Gestionar modelos entrenados

## Verificación

### Verificar que el Servidor Funciona

```bash
curl http://localhost:8000/api/health
```

Respuesta esperada:
```json
{"status": "ok"}
```

### Generar un Poema de Prueba

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "casa",
    "max_sentences": 5,
    "temperature": 0.7
  }'
```

## Próximos Pasos

- **[Entrenar un modelo personalizado](TRAINING.md)**: Aprende a entrenar modelos con tus propios poemas
- **[Usar el panel de administración](ADMIN_PANEL.md)**: Gestiona datasets y modelos
- **[Integrar con LM Studio](LM_STUDIO.md)**: Mejora la calidad con modelos avanzados
- **[Ver ejemplos](EXAMPLES.md)**: Explora diferentes tipos de directrices

## Solución de Problemas

### El servidor no inicia

- Verifica que el puerto 8000 esté libre: `lsof -i :8000`
- Asegúrate de estar en el entorno virtual: `poetry shell`

### Error al cargar el modelo

- La primera vez puede tardar mientras descarga el modelo (~500MB)
- Verifica tu conexión a internet
- El modelo se guarda en `~/.cache/huggingface/transformers/`

### La generación es lenta

- Es normal en la primera generación (carga del modelo)
- Considera usar LM Studio para mejor rendimiento
- Ver [LM Studio](LM_STUDIO.md) para más detalles

