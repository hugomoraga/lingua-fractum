# Ejemplos de Uso

Colección de ejemplos para usar la Plataforma de Poesía.

## Inicio Rápido

### 1. Iniciar el Servidor

```bash
poetry run uvicorn poema_algoritmo.main:app --reload
```

### 2. Abrir en el Navegador

Abre: `http://localhost:8000`

## Ejemplos de Directrices

### Conceptos Simples

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "casa",
    "max_sentences": 8,
    "temperature": 0.7
  }'
```

### Con Emoción

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "escribe un poema triste sobre la casa",
    "max_sentences": 10,
    "temperature": 0.7
  }'
```

### Directriz Compleja

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "soneto romántico sobre el amor, corto y con elementos de naturaleza",
    "max_sentences": 14,
    "temperature": 0.8
  }'
```

### Tema Poético

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "la noche estrellada",
    "max_sentences": 8,
    "temperature": 0.7
  }'
```

## Más Ejemplos

### Directrices con Estilo

- `"haiku sobre la primavera"`
- `"verso libre sobre la ciudad"`
- `"soneto sobre el tiempo"`
- `"poema en prosa sobre el mar"`

### Directrices con Emoción

- `"poema alegre sobre la amistad"`
- `"poema nostálgico sobre la infancia"`
- `"poema oscuro sobre la soledad"`
- `"poema melancólico sobre el pasado"`

### Directrices con Elementos

- `"poema sobre el mar, con luna y estrellas"`
- `"poema sobre la montaña, con viento y naturaleza"`
- `"poema sobre la ciudad, con colores y ruido"`
- `"poema sobre el bosque, con animales y silencio"`

### Directrices Complejas

- `"soneto romántico sobre el amor, triste y corto, con elementos de naturaleza y luna"`
- `"verso libre moderno sobre la ciudad, alegre y medio, con colores y movimiento"`
- `"haiku sereno sobre la noche, corto, con estrellas y silencio"`
- `"poema épico sobre la batalla, largo y dramático, con héroes y espadas"`

## Parámetros

### max_sentences

Controla la longitud del poema en número de frases:

- **3-5**: Poemas cortos (haikus, poemas breves)
- **6-10**: Longitud media (recomendado)
- **11-15**: Poemas largos (sonetos, poemas extensos)
- **16-20**: Poemas muy largos (poemas épicos)

### temperature

Controla la creatividad y variabilidad:

- **0.5-0.6**: Poesía más conservadora y predecible
- **0.7-0.8**: Balance entre coherencia y creatividad (recomendado)
- **0.9-1.0**: Más creativo y variado
- **1.1-1.5**: Muy creativo pero puede ser menos coherente

## Ejemplos en Python

### Generar un Poema

```python
import requests

def generar_poema(directriz, max_sentences=8, temperature=0.7):
    response = requests.post(
        "http://localhost:8000/api/generate",
        json={
            "input_text": directriz,
            "max_sentences": max_sentences,
            "temperature": temperature
        }
    )
    return response.json()

# Ejemplo
resultado = generar_poema("casa")
print(resultado["poem"])
```

### Generar Múltiples Poemas

```python
import requests

directrices = [
    "casa",
    "amor",
    "noche",
    "mar"
]

for directriz in directrices:
    response = requests.post(
        "http://localhost:8000/api/generate",
        json={
            "input_text": directriz,
            "max_sentences": 8,
            "temperature": 0.7
        }
    )
    resultado = response.json()
    print(f"\n=== {directriz} ===")
    print(resultado["poem"])
```

### Experimentar con Parámetros

```python
import requests

directriz = "casa"

# Probar diferentes temperaturas
for temp in [0.5, 0.7, 0.9, 1.2]:
    response = requests.post(
        "http://localhost:8000/api/generate",
        json={
            "input_text": directriz,
            "max_sentences": 8,
            "temperature": temp
        }
    )
    resultado = response.json()
    print(f"\n=== Temperatura: {temp} ===")
    print(resultado["poem"])
```

## Consejos

1. **Directrices específicas**: Mientras más específica sea tu directriz, mejor será el resultado
2. **Temperatura baja (0.5-0.7)**: Para poesía más coherente y predecible
3. **Temperatura alta (0.8-1.2)**: Para poesía más creativa y variada
4. **Con LM Studio**: Obtendrás mejor interpretación de directrices y poesía de mayor calidad
5. **Sin LM Studio**: El sistema funciona perfectamente con el modelo local

## Verificar Estado

### Verificar Salud del Servidor

```bash
curl http://localhost:8000/api/health
```

### Verificar Estado de LM Studio

```bash
curl http://localhost:8000/api/lm-studio-status
```

## Solución de Problemas

### El servidor no responde

- Verifica que esté corriendo: `curl http://localhost:8000/api/health`
- Revisa los logs del servidor
- Verifica que el puerto 8000 esté libre

### LM Studio no se detecta

- Verifica que LM Studio esté corriendo
- Verifica que el servidor local esté iniciado en LM Studio
- Revisa la URL: `http://localhost:1234/v1`

### La generación es lenta

- Normal con modelos grandes
- Con LM Studio puede tardar más pero la calidad es mejor
- El modelo local es más rápido pero menos potente
- La primera generación siempre tarda más (carga del modelo)

