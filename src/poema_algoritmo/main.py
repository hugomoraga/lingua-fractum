from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import os

from .poem_generator import PoemGenerator

app = FastAPI(title="Plataforma de Poesía")

# Montar archivos estáticos
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Inicializar el generador de poemas
poem_generator = PoemGenerator()

class PoemRequest(BaseModel):
    input_text: str
    max_length: Optional[int] = 200
    temperature: Optional[float] = 0.9

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
    """Generar un poema basado en el input del usuario"""
    try:
        if not request.input_text or not request.input_text.strip():
            raise HTTPException(status_code=400, detail="El texto de entrada no puede estar vacío")
        
        poem = poem_generator.generate(
            prompt=request.input_text,
            max_length=request.max_length,
            temperature=request.temperature
        )
        
        return JSONResponse({
            "poem": poem,
            "success": True
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el poema: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Endpoint de salud"""
    return {"status": "ok", "message": "Plataforma de poesía funcionando"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
