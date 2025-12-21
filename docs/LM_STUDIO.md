# Integración con LM Studio

Guía para usar LM Studio con la Plataforma de Poesía para mejorar la calidad de generación.

## ¿Qué es LM Studio?

LM Studio es una herramienta que permite ejecutar modelos de lenguaje grandes (LLMs) localmente en tu computadora, sin necesidad de conexión a internet.

## Ventajas

1. **Mejor interpretación**: Entiende directrices complejas con mayor precisión
2. **Mayor calidad**: Modelos más grandes = poesía más coherente y creativa
3. **Completamente local**: Todo funciona sin conexión a internet
4. **Modelos avanzados**: Acceso a modelos más potentes que GPT-2

## Instalación

### 1. Descargar LM Studio

Descarga desde: https://lmstudio.ai

Disponible para:
- Windows
- macOS
- Linux

### 2. Descargar un Modelo en Español

1. Abre LM Studio
2. Ve a "Discover"
3. Busca modelos en español (recomendados):
   - Llama 2/3 (versiones en español)
   - Mistral (versiones en español)
   - Cualquier modelo entrenado en español
4. Descarga el modelo que prefieras

### 3. Cargar el Modelo

1. Ve a la pestaña "Chat" en LM Studio
2. Selecciona el modelo descargado
3. Carga el modelo (puede tardar unos minutos la primera vez)

### 4. Iniciar el Servidor Local

1. En LM Studio, ve a "Local Server" (o "Server")
2. Haz clic en "Start Server"
3. El servidor se iniciará en `http://localhost:1234` por defecto

## Uso

### Modo Automático (Recomendado)

Simplemente inicia LM Studio con un modelo cargado y el servidor activo, luego ejecuta:

```bash
poetry run uvicorn poema_algoritmo.main:app --reload
```

El sistema detectará automáticamente si LM Studio está disponible y lo usará.

### Configurar URL Personalizada

Si LM Studio está en un puerto diferente:

```bash
LM_STUDIO_URL=http://localhost:PUERTO/v1 poetry run uvicorn poema_algoritmo.main:app --reload
```

### Desactivar LM Studio

Si prefieres usar solo el modelo local:

```bash
USE_LM_STUDIO=false poetry run uvicorn poema_algoritmo.main:app --reload
```

O simplemente no inicies el servidor de LM Studio.

## Verificación

### Verificar Estado

En la interfaz web, verás un indicador en el header:
- **~ Verde**: LM Studio activo y disponible
- **~ Gris**: LM Studio inactivo (usando modelo local)

### Verificar mediante API

```bash
curl http://localhost:8000/api/lm-studio-status
```

Respuesta esperada:
```json
{
  "available": true,
  "using_lm_studio": true,
  "message": "LM Studio disponible"
}
```

## Comparación

### Interpretación de Directrices

**Con LM Studio**:
- Entiende directrices complejas: `"escribe un soneto triste sobre la casa, corto y con naturaleza"`
- Interpreta matices y emociones
- Sigue instrucciones específicas

**Sin LM Studio**:
- Usa reglas básicas
- Puede perder algunos matices
- Funciona pero con menor precisión

### Generación de Poesía

**Con LM Studio**:
- Modelos más grandes (7B+ parámetros)
- Mejor coherencia
- Poesía más creativa y natural
- Mejor seguimiento de directrices

**Sin LM Studio**:
- Usa GPT-2 local (más pequeño)
- Funciona offline
- Calidad aceptable pero limitada

## Configuración Avanzada

### Variables de Entorno

```bash
# URL de LM Studio (default: http://localhost:1234/v1)
export LM_STUDIO_URL=http://localhost:1234/v1

# Desactivar LM Studio completamente
export USE_LM_STUDIO=false
```

### En el Código

```python
from poema_algoritmo.poem_generator import PoemGenerator

# Crear generador sin LM Studio
generator = PoemGenerator(use_lm_studio=False)

# Generar con preferencia por modelo local
poem, directive = generator.generate(
    prompt="casa",
    prefer_lm_studio=False
)
```

## Ejemplos

### Directrices Simples

```
"casa"
```
→ Funciona igual con o sin LM Studio

### Directrices Complejas

```
"escribe un soneto romántico sobre el amor, triste y corto, con elementos de naturaleza"
```

**Con LM Studio**: Interpreta perfectamente todos los elementos
**Sin LM Studio**: Puede perder algunos matices

### Generación de Alta Calidad

Con un modelo grande en LM Studio (7B+ parámetros), obtendrás:
- Mejor coherencia
- Mejor seguimiento de directrices
- Poesía más creativa y natural
- Menos repeticiones

## Notas Importantes

1. **Rendimiento**: Los modelos grandes requieren más RAM y pueden ser más lentos
2. **Primera vez**: La primera generación puede tardar más mientras el modelo se carga
3. **Fallback automático**: Si LM Studio no está disponible, el sistema usa automáticamente el modelo local
4. **Modelos en español**: Para mejores resultados, usa modelos entrenados en español

## Solución de Problemas

### "LM Studio no disponible"

**Solución**:
- Verifica que LM Studio esté corriendo
- Verifica que el servidor local esté iniciado
- Verifica que el puerto sea el correcto (default: 1234)
- Revisa la URL en la configuración

### "Error al conectar con LM Studio"

**Solución**:
- Verifica la URL: `http://localhost:1234/v1`
- Verifica que el modelo esté cargado en LM Studio
- Revisa los logs de LM Studio
- Verifica que no haya firewall bloqueando la conexión

### "Generación muy lenta"

**Solución**:
- Los modelos grandes son más lentos (normal)
- Considera usar un modelo más pequeño
- O usa el modelo local con `prefer_lm_studio=false`
- Verifica que tengas suficiente RAM disponible

### El indicador muestra estado incorrecto

**Solución**:
- Refresca la página
- Verifica que el servidor esté corriendo
- Revisa los logs del servidor para errores

## Recursos

- [LM Studio Documentation](https://lmstudio.ai/docs)
- [Modelos recomendados para español](https://huggingface.co/models?language=es)
- [Tutorial de LM Studio](https://www.youtube.com/watch?v=mWVF-ubKaJc)

