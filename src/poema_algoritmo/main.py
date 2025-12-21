from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import os

from .poem_generator import PoemGenerator
from .admin import router as admin_router

app = FastAPI(title="Plataforma de Poesía con Agente Inteligente")

# Registrar router de administración
app.include_router(admin_router)

# Montar archivos estáticos
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Inicializar el generador de poemas (lazy loading para evitar cargar modelo al inicio)
poem_generator = None

def get_poem_generator():
    """Obtiene o crea el generador de poemas (lazy initialization)"""
    global poem_generator
    if poem_generator is None:
        poem_generator = PoemGenerator()
    return poem_generator

class PoemRequest(BaseModel):
    input_text: str
    max_sentences: Optional[int] = 8  # Número de frases objetivo
    max_length: Optional[int] = None  # Deprecated: usar max_sentences
    temperature: Optional[float] = 0.7  # Reducido para mejor coherencia
    use_agent: Optional[bool] = True  # Usar agente para interpretar directrices
    prefer_lm_studio: Optional[bool] = True  # Preferir LM Studio si está disponible

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Servir la página principal"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return """
    <html>
        <head><title>Plataforma de Poesía</title></head>
        <body><h1>Plataforma de Poesía</h1><p>Interfaz no encontrada</p></body>
    </html>
    """

@app.post("/api/generate")
async def generate_poem(request: PoemRequest):
    """
    Generar un poema basado en el input del usuario.
    El agente interpreta directrices en lenguaje natural.
    
    Ejemplos de directrices:
    - "casa" (simple)
    - "escribe un poema triste sobre la casa"
    - "soneto romántico sobre el amor, corto y con naturaleza"
    - "verso libre sobre la ciudad, alegre y moderno"
    """
    try:
        if not request.input_text or not request.input_text.strip():
            raise HTTPException(status_code=400, detail="El texto de entrada no puede estar vacío")
        
        # Convertir max_sentences a max_length aproximado (65 caracteres por frase promedio)
        # Usar max_sentences si está disponible, sino max_length (backward compatibility)
        if request.max_sentences:
            avg_chars_per_sentence = 65
            calculated_max_length = request.max_sentences * avg_chars_per_sentence
        else:
            calculated_max_length = request.max_length or 200
        
        generator = get_poem_generator()
        poem, directive = generator.generate(
            prompt=request.input_text,
            max_length=calculated_max_length,
            temperature=request.temperature,
            use_agent=request.use_agent,
            prefer_lm_studio=request.prefer_lm_studio
        )
        
        response_data = {
            "poem": poem,
            "success": True
        }
        
        # Incluir información de la directiva interpretada si está disponible
        if directive and request.use_agent:
            response_data["directive"] = {
                "main_concept": directive.main_concept,
                "style": directive.style,
                "emotion": directive.emotion,
                "length": directive.length,
                "elements": directive.elements,
                "summary": generator.agent.get_directive_summary(directive)
            }
        
        return JSONResponse(response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el poema: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Endpoint de salud"""
    return {"status": "ok", "message": "Plataforma de poesía funcionando"}

@app.get("/api/lm-studio-status")
async def lm_studio_status():
    """Verifica el estado de LM Studio"""
    try:
        generator = get_poem_generator()
        lm_available = False
        if generator.lm_studio_client:
            lm_available = generator.lm_studio_client.is_available()
        
        return {
            "available": lm_available,
            "using_lm_studio": lm_available and generator.use_lm_studio,
            "message": "LM Studio disponible" if lm_available else "LM Studio no disponible"
        }
    except Exception as e:
        return {
            "available": False,
            "using_lm_studio": False,
            "message": f"Error al verificar: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
