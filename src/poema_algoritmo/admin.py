"""
Panel de administración para gestionar datasets y entrenar modelos
"""
import os
import json
import shutil
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import json

from .train_model import PoetryTrainer
from .epub_processor import EPUBProcessor

router = APIRouter(prefix="/admin", tags=["admin"])

# Directorios
DATA_DIR = Path("data")
MODELS_DIR = Path("models")
EPUB_DIR = DATA_DIR / "epub"

# Asegurar que los directorios existen
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
EPUB_DIR.mkdir(exist_ok=True)


class TrainingRequest(BaseModel):
    """Request para iniciar entrenamiento"""
    poems_file: str
    output_dir: str = "models/poetry_model"
    epochs: int = 5
    batch_size: int = 4
    learning_rate: float = 5e-5
    base_model: Optional[str] = None


class DatasetInfo(BaseModel):
    """Información de un dataset"""
    name: str
    path: str
    size: int
    poems_count: Optional[int] = None
    created: Optional[str] = None


@router.get("/", response_class=HTMLResponse)
async def admin_panel():
    """Panel principal de administración"""
    html_path = Path(__file__).parent / "static" / "admin.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return """
    <html>
        <head><title>Panel de Administración</title></head>
        <body>
            <h1>Panel de Administración</h1>
            <p>Interfaz de administración no encontrada</p>
        </body>
    </html>
    """


@router.get("/api/datasets")
async def list_datasets():
    """Lista todos los datasets disponibles"""
    datasets = []
    
    # Buscar archivos de poemas
    for file_path in DATA_DIR.glob("*.txt"):
        try:
            stat = file_path.stat()
            # Intentar contar poemas (aproximado)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Contar separadores (soporta === POEMA === y === POEMA X ===)
                separator_pattern = r'===+\s*POEMA\s*(?:\d+)?\s*===+'
                has_separators = bool(re.search(separator_pattern, content, re.IGNORECASE))
                
                if has_separators:
                    # Contar todas las variantes del separador
                    matches = re.findall(separator_pattern, content, re.IGNORECASE)
                    poems_count = len(matches)
                else:
                    # Formato libre: usar función optimizada (sin cargar modelo)
                    extracted_poems = _extract_poems_free_format(content)
                    poems_count = len(extracted_poems)
            
            datasets.append({
                "name": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "poems_count": poems_count,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        except Exception as e:
            print(f"Error al leer {file_path}: {e}")
    
    return {"datasets": datasets}


@router.put("/api/datasets/{filename}/rename")
async def rename_dataset(filename: str, new_name: str = Form(...)):
    """Renombra un dataset"""
    file_path = DATA_DIR / filename
    new_file_path = DATA_DIR / new_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    if new_file_path.exists():
        raise HTTPException(status_code=400, detail="Ya existe un dataset con ese nombre")
    
    # Validar nombre (solo letras, números, guiones y guiones bajos, debe terminar en .txt)
    if not new_name.endswith('.txt'):
        new_name = new_name + '.txt'
        new_file_path = DATA_DIR / new_name
    
    if not re.match(r'^[a-zA-Z0-9_-]+\.txt$', new_name):
        raise HTTPException(status_code=400, detail="Nombre inválido. Solo letras, números, guiones y guiones bajos")
    
    # Proteger poems.txt
    if filename == "poems.txt":
        raise HTTPException(status_code=403, detail="No se puede renombrar el dataset principal poems.txt")
    
    try:
        file_path.rename(new_file_path)
        return {
            "success": True,
            "message": f"Dataset renombrado a {new_name}",
            "old_name": filename,
            "new_name": new_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al renombrar: {str(e)}")


def _extract_poems_free_format(content: str) -> List[Dict]:
    """
    Extrae poemas de formato libre sin cargar el modelo
    Optimizado para visualización (más permisivo que entrenamiento)
    """
    import re
    
    poems = []
    content_lines = content.split('\n')
    
    # Buscar donde terminan los metadatos iniciales
    start_idx = 0
    for i, line in enumerate(content_lines[:200]):
        line_upper = line.strip().upper()
        if any(keyword in line_upper for keyword in ['AL LECTOR', 'SPLEEN', 'BENDICIÓN', 'EL ALBATROS', 'PRÓLOGO']):
            start_idx = i
            break
    
    if start_idx > 0:
        content_lines = content_lines[start_idx:]
    
    current_poem_lines = []
    empty_line_count = 0
    poem_index = 0
    
    for i, line in enumerate(content_lines):
        line_stripped = line.strip()
        
        if not line_stripped:
            empty_line_count += 1
            # Si hay 3+ líneas vacías consecutivas, probablemente es fin de poema
            if empty_line_count >= 3 and current_poem_lines:
                poem_text = '\n'.join(current_poem_lines).strip()
                if poem_text and len(poem_text) > 20:
                    poems.append({
                        "id": poem_index,
                        "text": poem_text,
                        "length": len(poem_text)
                    })
                    poem_index += 1
                current_poem_lines = []
                empty_line_count = 0
        else:
            # Filtrar metadatos obvios
            line_lower = line_stripped.lower()
            is_metadata = (
                re.match(r'^\d{4}\s*\.?\s*$', line_stripped) or  # Años solos
                (line_stripped.isupper() and len(line_stripped) < 50 and i < 50) or  # Títulos de sección al inicio
                any(word in line_lower for word in ['charles baudelaire', 'las flores del mal', 'epublibre', 'editor digital'])
            )
            
            if not is_metadata:
                empty_line_count = 0
                current_poem_lines.append(line)
    
    # Agregar último poema
    if current_poem_lines:
        poem_text = '\n'.join(current_poem_lines).strip()
        if poem_text and len(poem_text) > 20:
            poems.append({
                "id": poem_index,
                "text": poem_text,
                "length": len(poem_text)
            })
    
    return poems


def _extract_poems_free_format_with_positions(content: str) -> Tuple[List[Dict], List[Tuple[int, int]]]:
    """
    Extrae poemas de formato libre y retorna también sus posiciones (start_line, end_line)
    para poder reconstruir el archivo correctamente
    """
    import re
    
    poems = []
    positions = []
    content_lines = content.split('\n')
    original_lines = content_lines.copy()
    
    # Buscar donde terminan los metadatos iniciales
    start_idx = 0
    for i, line in enumerate(content_lines[:200]):
        line_upper = line.strip().upper()
        if any(keyword in line_upper for keyword in ['AL LECTOR', 'SPLEEN', 'BENDICIÓN', 'EL ALBATROS', 'PRÓLOGO']):
            start_idx = i
            break
    
    if start_idx > 0:
        content_lines = content_lines[start_idx:]
        offset = start_idx
    else:
        offset = 0
    
    current_poem_lines = []
    current_start_line = offset
    empty_line_count = 0
    poem_index = 0
    
    for i, line in enumerate(content_lines):
        line_stripped = line.strip()
        actual_line_num = i + offset
        
        if not line_stripped:
            empty_line_count += 1
            # Si hay 3+ líneas vacías consecutivas, probablemente es fin de poema
            if empty_line_count >= 3 and current_poem_lines:
                poem_text = '\n'.join(current_poem_lines).strip()
                if poem_text and len(poem_text) > 20:
                    poems.append({
                        "id": poem_index,
                        "text": poem_text,
                        "length": len(poem_text)
                    })
                    positions.append((current_start_line, actual_line_num - 3))
                    poem_index += 1
                current_poem_lines = []
                empty_line_count = 0
        else:
            # Filtrar metadatos obvios
            line_lower = line_stripped.lower()
            is_metadata = (
                re.match(r'^\d{4}\s*\.?\s*$', line_stripped) or  # Años solos
                (line_stripped.isupper() and len(line_stripped) < 50 and i < 50) or  # Títulos de sección al inicio
                any(word in line_lower for word in ['charles baudelaire', 'las flores del mal', 'epublibre', 'editor digital'])
            )
            
            if not is_metadata:
                if not current_poem_lines:
                    current_start_line = actual_line_num
                empty_line_count = 0
                current_poem_lines.append(line)
    
    # Agregar último poema
    if current_poem_lines:
        poem_text = '\n'.join(current_poem_lines).strip()
        if poem_text and len(poem_text) > 20:
            poems.append({
                "id": poem_index,
                "text": poem_text,
                "length": len(poem_text)
            })
            positions.append((current_start_line, len(original_lines)))
    
    return poems, positions


@router.get("/api/datasets/{filename}/poems")
async def get_dataset_poems(
    filename: str, 
    page: int = Query(1, ge=1), 
    per_page: int = Query(50, ge=1, le=100)
):
    """
    Obtiene poemas de un dataset con paginación
    
    Args:
        filename: Nombre del archivo
        page: Número de página (empezando en 1)
        per_page: Poemas por página (máximo 100)
    """
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    # Limitar per_page
    per_page = min(max(1, per_page), 100)
    page = max(1, page)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Detectar formato: ¿tiene separadores con === POEMA ===?
        # Buscar tanto "=== POEMA ===" como "=== POEMA X ===" para compatibilidad
        separator = "=== POEMA ==="
        separator_pattern = r'===+\s*POEMA\s*(?:\d+)?\s*===+'
        has_separators = bool(re.search(separator_pattern, content, re.IGNORECASE))
        
        if has_separators:
            # Formato con separadores explícitos (soporta === POEMA === y === POEMA X ===)
            # Dividir por cualquier variante del separador
            poems_raw = re.split(separator_pattern, content, flags=re.IGNORECASE)
            
            all_poems = []
            poem_index = 0
            for poem_raw in poems_raw:
                poem_text = poem_raw.strip()
                # Filtrar líneas que son solo el separador o metadatos
                lines = [line.strip() for line in poem_text.split('\n') if line.strip()]
                # Eliminar líneas que son solo separadores o números
                filtered_lines = [
                    line for line in lines 
                    if not re.match(r'^===+\s*POEMA\s*(?:\d+)?\s*===+$', line, re.IGNORECASE)
                    and not re.match(r'^\d+$', line)
                ]
                poem_text = '\n'.join(filtered_lines).strip()
                
                if poem_text and len(poem_text) > 10:
                    all_poems.append({
                        "id": poem_index,
                        "text": poem_text,
                        "length": len(poem_text)
                    })
                    poem_index += 1
        else:
            # Formato libre: usar función optimizada (sin cargar modelo)
            all_poems = _extract_poems_free_format(content)
        
        # Paginación
        total = len(all_poems)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        poems_page = all_poems[start_idx:end_idx]
        
        return {
            "filename": filename,
            "poems": poems_page,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page if total > 0 else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el dataset: {str(e)}")


@router.get("/api/datasets/{filename}/poems/{poem_id}")
async def get_poem_by_id(filename: str, poem_id: int):
    """Obtiene un poema específico por ID (sin paginación, para edición)"""
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Detectar formato (soporta === POEMA === y === POEMA X ===)
        separator = "=== POEMA ==="
        separator_pattern = r'===+\s*POEMA\s*(?:\d+)?\s*===+'
        has_separators = bool(re.search(separator_pattern, content, re.IGNORECASE))
        
        if has_separators:
            # Dividir por cualquier variante del separador
            poems_raw = re.split(separator_pattern, content, flags=re.IGNORECASE)
            all_poems = []
            poem_index = 0
            for poem_raw in poems_raw:
                poem_text = poem_raw.strip()
                # Filtrar líneas que son solo separadores
                lines = [line.strip() for line in poem_text.split('\n') if line.strip()]
                filtered_lines = [
                    line for line in lines 
                    if not re.match(r'^===+\s*POEMA\s*(?:\d+)?\s*===+$', line, re.IGNORECASE)
                    and not re.match(r'^\d+$', line)
                ]
                poem_text = '\n'.join(filtered_lines).strip()
                if poem_text and len(poem_text) > 10:
                    all_poems.append({
                        "id": poem_index,
                        "text": poem_text,
                        "length": len(poem_text)
                    })
                    poem_index += 1
        else:
            all_poems = _extract_poems_free_format(content)
        
        # Buscar poema por ID
        poem = next((p for p in all_poems if p["id"] == poem_id), None)
        
        if poem is None:
            raise HTTPException(status_code=404, detail=f"Poema con ID {poem_id} no encontrado")
        
        return poem
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el dataset: {str(e)}")


@router.put("/api/datasets/{filename}/poems/{poem_id}")
async def update_poem(filename: str, poem_id: int, poem: str = Form(...)):
    """Actualiza un poema específico en un dataset"""
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    if not poem or not poem.strip():
        raise HTTPException(status_code=400, detail="El poema no puede estar vacío")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content_lines = content.split('\n')
        
        # Detectar formato (soporta === POEMA === y === POEMA X ===)
        separator = "=== POEMA ==="
        separator_pattern = r'===+\s*POEMA\s*(?:\d+)?\s*===+'
        has_separators = bool(re.search(separator_pattern, content, re.IGNORECASE))
        
        if has_separators:
            # Formato con separadores (dividir por cualquier variante)
            poems_raw = re.split(separator_pattern, content, flags=re.IGNORECASE)
            valid_poems = []
            for poem_raw in poems_raw:
                poem_text = poem_raw.strip()
                # Filtrar líneas que son solo separadores
                lines = [line.strip() for line in poem_text.split('\n') if line.strip()]
                filtered_lines = [
                    line for line in lines 
                    if not re.match(r'^===+\s*POEMA\s*(?:\d+)?\s*===+$', line, re.IGNORECASE)
                ]
                poem_text = '\n'.join(filtered_lines).strip()
                if poem_text and len(poem_text) > 10:
                    valid_poems.append(poem_text)
            
            if poem_id < 0 or poem_id >= len(valid_poems):
                raise HTTPException(status_code=404, detail="Poema no encontrado")
            
            # Actualizar el poema específico
            valid_poems[poem_id] = poem.strip()
            
            # Reconstruir el contenido con formato estándar
            new_content = ""
            for i, poem_text in enumerate(valid_poems):
                if i > 0:
                    new_content += "\n\n"
                new_content += separator + "\n\n" + poem_text + "\n"
        else:
            # Formato libre: usar función con posiciones
            extracted_poems, positions = _extract_poems_free_format_with_positions(content)
            
            if poem_id < 0 or poem_id >= len(extracted_poems):
                raise HTTPException(status_code=404, detail="Poema no encontrado")
            
            # Obtener posición del poema a actualizar
            start_line, end_line = positions[poem_id]
            
            # Reconstruir: antes del poema + nuevo poema + después del poema
            before_lines = content_lines[:start_line]
            after_lines = content_lines[end_line:]
            
            # Nuevo poema con separación adecuada
            new_poem_lines = poem.strip().split('\n')
            
            # Reconstruir manteniendo estructura
            new_content_lines = before_lines + new_poem_lines + [''] + [''] + after_lines
            new_content = '\n'.join(new_content_lines)
        
        # Escribir de vuelta
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "success": True,
            "message": f"Poema {poem_id} actualizado en {filename}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el poema: {str(e)}")


@router.delete("/api/datasets/{filename}/poems/batch-delete")
async def delete_poems_batch(filename: str, request: Request):
    """Elimina múltiples poemas de un dataset"""
    try:
        body = await request.json()
        poem_ids = body.get('poem_ids', [])
    except:
        raise HTTPException(status_code=400, detail="Cuerpo de solicitud inválido")
    
    if not poem_ids:
        raise HTTPException(status_code=400, detail="No se proporcionaron IDs de poemas para eliminar")
    
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content_lines = content.split('\n')
        
        # Detectar formato (soporta === POEMA === y === POEMA X ===)
        separator = "=== POEMA ==="
        separator_pattern = r'===+\s*POEMA\s*(?:\d+)?\s*===+'
        has_separators = bool(re.search(separator_pattern, content, re.IGNORECASE))
        
        if has_separators:
            # Formato con separadores (dividir por cualquier variante)
            poems_raw = re.split(separator_pattern, content, flags=re.IGNORECASE)
            valid_poems = []
            for poem_raw in poems_raw:
                poem_text = poem_raw.strip()
                # Filtrar líneas que son solo separadores
                lines = [line.strip() for line in poem_text.split('\n') if line.strip()]
                filtered_lines = [
                    line for line in lines 
                    if not re.match(r'^===+\s*POEMA\s*(?:\d+)?\s*===+$', line, re.IGNORECASE)
                ]
                poem_text = '\n'.join(filtered_lines).strip()
                if poem_text and len(poem_text) > 10:
                    valid_poems.append(poem_text)
            
            # Eliminar poemas seleccionados (ordenar IDs descendente para evitar problemas de índice)
            poem_ids_sorted = sorted(set(poem_ids), reverse=True)
            deleted_count = 0
            for poem_id in poem_ids_sorted:
                if 0 <= poem_id < len(valid_poems):
                    valid_poems.pop(poem_id)
                    deleted_count += 1
            
            if deleted_count == 0:
                raise HTTPException(status_code=404, detail="No se encontraron poemas válidos para eliminar")
            
            # Reconstruir el contenido con formato estándar
            new_content = ""
            for i, poem_text in enumerate(valid_poems):
                if i > 0:
                    new_content += "\n\n"
                new_content += separator + "\n\n" + poem_text + "\n"
        else:
            # Formato libre: usar función con posiciones
            extracted_poems, positions = _extract_poems_free_format_with_positions(content)
            
            # Eliminar poemas seleccionados (ordenar IDs descendente)
            poem_ids_sorted = sorted(set(poem_ids), reverse=True)
            deleted_positions = []
            for poem_id in poem_ids_sorted:
                if 0 <= poem_id < len(positions):
                    deleted_positions.append(positions[poem_id])
                    del positions[poem_id]
                    del extracted_poems[poem_id]
            
            if not deleted_positions:
                raise HTTPException(status_code=404, detail="No se encontraron poemas válidos para eliminar")
            
            # Reconstruir: eliminar las líneas de los poemas eliminados
            deleted_positions.sort(key=lambda x: x[0], reverse=True)  # Ordenar por línea de inicio descendente
            for start_line, end_line in deleted_positions:
                content_lines = content_lines[:start_line] + content_lines[end_line:]
            
            new_content = '\n'.join(content_lines)
        
        # Escribir de vuelta
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "success": True,
            "message": f"{deleted_count} poema(s) eliminado(s) de {filename}",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar poemas: {str(e)}")


@router.delete("/api/datasets/{filename}/poems/{poem_id}")
async def delete_poem(filename: str, poem_id: int):
    """Elimina un poema específico de un dataset"""
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content_lines = content.split('\n')
        
        # Detectar formato (soporta === POEMA === y === POEMA X ===)
        separator = "=== POEMA ==="
        separator_pattern = r'===+\s*POEMA\s*(?:\d+)?\s*===+'
        has_separators = bool(re.search(separator_pattern, content, re.IGNORECASE))
        
        if has_separators:
            # Formato con separadores (dividir por cualquier variante)
            poems_raw = re.split(separator_pattern, content, flags=re.IGNORECASE)
            valid_poems = []
            for poem_raw in poems_raw:
                poem_text = poem_raw.strip()
                # Filtrar líneas que son solo separadores
                lines = [line.strip() for line in poem_text.split('\n') if line.strip()]
                filtered_lines = [
                    line for line in lines 
                    if not re.match(r'^===+\s*POEMA\s*(?:\d+)?\s*===+$', line, re.IGNORECASE)
                ]
                poem_text = '\n'.join(filtered_lines).strip()
                if poem_text and len(poem_text) > 10:
                    valid_poems.append(poem_text)
            
            if poem_id < 0 or poem_id >= len(valid_poems):
                raise HTTPException(status_code=404, detail="Poema no encontrado")
            
            # Eliminar el poema específico
            valid_poems.pop(poem_id)
            
            # Reconstruir el contenido con formato estándar
            new_content = ""
            for i, poem_text in enumerate(valid_poems):
                if i > 0:
                    new_content += "\n\n"
                new_content += separator + "\n\n" + poem_text + "\n"
        else:
            # Formato libre: usar función con posiciones
            extracted_poems, positions = _extract_poems_free_format_with_positions(content)
            
            if poem_id < 0 or poem_id >= len(extracted_poems):
                raise HTTPException(status_code=404, detail="Poema no encontrado")
            
            # Obtener posición del poema a eliminar
            start_line, end_line = positions[poem_id]
            
            # Reconstruir: antes del poema + después del poema (sin el poema eliminado)
            before_lines = content_lines[:start_line]
            after_lines = content_lines[end_line:]
            
            # Reconstruir manteniendo estructura
            new_content_lines = before_lines + after_lines
            new_content = '\n'.join(new_content_lines)
        
        # Escribir de vuelta
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "success": True,
            "message": f"Poema {poem_id} eliminado de {filename}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el poema: {str(e)}")


@router.post("/api/datasets/{filename}/clean")
async def clean_dataset(filename: str):
    """Limpia un dataset eliminando notas de pie de página y otros artefactos"""
    import re
    
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Limpiar notas de pie de página (números entre corchetes)
        cleaned_content = re.sub(r'\[\d+\]', '', content)
        cleaned_content = re.sub(r'\s*\[\d+\]\s*', ' ', cleaned_content)
        
        # Limpiar espacios múltiples
        cleaned_content = re.sub(r' +', ' ', cleaned_content)
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
        
        # Escribir de vuelta
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        return {
            "success": True,
            "message": f"Dataset {filename} limpiado correctamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al limpiar el dataset: {str(e)}")


@router.post("/api/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Sube un nuevo dataset"""
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .txt")
    
    file_path = DATA_DIR / file.filename
    
    # Guardar archivo
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    return {
        "success": True,
        "message": f"Dataset {file.filename} subido correctamente",
        "path": str(file_path)
    }


@router.post("/api/datasets/upload-epub")
async def upload_and_convert_epub(
    file: UploadFile = File(...),
    dataset_name: str = Form(None)
):
    """
    Sube un archivo EPUB y lo convierte a dataset .txt
    
    Args:
        file: Archivo EPUB a procesar
        dataset_name: Nombre opcional para el dataset (sin extensión). 
                     Si no se proporciona, se usa el nombre del archivo EPUB
    """
    if not file.filename.endswith('.epub'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .epub")
    
    import tempfile
    
    # Crear nombre del dataset
    if dataset_name:
        output_filename = dataset_name.strip()
        if not output_filename.endswith('.txt'):
            output_filename = output_filename + '.txt'
    else:
        # Usar el nombre del EPUB sin extensión
        output_filename = Path(file.filename).stem + '.txt'
    
    output_path = DATA_DIR / output_filename
    
    # Verificar si ya existe
    if output_path.exists():
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe un dataset con el nombre {output_filename}. Por favor, elige otro nombre."
        )
    
    # Guardar EPUB temporalmente
    temp_epub_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_epub_path = temp_file.name
        
        # Procesar EPUB
        processor = EPUBProcessor()
        poems = processor.process_epub_file(temp_epub_path)
        
        if not poems:
            raise HTTPException(
                status_code=400,
                detail="No se encontraron poemas en el archivo EPUB. Verifica que el archivo contenga poesías."
            )
        
        # Guardar como dataset .txt con formato estándar (sin números)
        separator = "=== POEMA ==="
        with open(output_path, 'w', encoding='utf-8') as f:
            for poem in poems:
                poem_cleaned = poem.strip()
                if poem_cleaned:
                    f.write(separator + "\n\n")
                    f.write(poem_cleaned)
                    f.write("\n\n\n")
        
        return {
            "success": True,
            "message": f"EPUB convertido correctamente. {len(poems)} poemas extraídos.",
            "filename": output_filename,
            "poems_count": len(poems),
            "path": str(output_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al procesar EPUB: {str(e)}")
    finally:
        # Limpiar archivo temporal
        if temp_epub_path and os.path.exists(temp_epub_path):
            try:
                os.unlink(temp_epub_path)
            except:
                pass


@router.post("/api/datasets/{filename}/add-poem")
async def add_poem_to_dataset(filename: str, poem: str = Form(...)):
    """Agrega un poema a un dataset existente"""
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    if not poem or not poem.strip():
        raise HTTPException(status_code=400, detail="El poema no puede estar vacío")
    
    # Leer el contenido actual
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el dataset: {str(e)}")
    
    # Agregar el nuevo poema con separador
    poem_cleaned = poem.strip()
    separator = "=== POEMA ==="
    
    # Si el archivo está vacío, no agregar separador al inicio
    if content.strip():
        # Si el archivo no termina en nueva línea, agregar una
        if not content.endswith('\n'):
            content += '\n'
        new_content = content + "\n\n" + separator + "\n\n" + poem_cleaned + "\n"
    else:
        # Archivo vacío, agregar solo el poema con separador al inicio
        new_content = separator + "\n\n" + poem_cleaned + "\n"
    
    # Escribir de vuelta
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al escribir el dataset: {str(e)}")
    
    return {
        "success": True,
        "message": f"Poema agregado a {filename}",
        "poem_length": len(poem_cleaned)
    }


@router.post("/api/datasets/create")
async def create_dataset(name: str = Form(...)):
    """Crea un nuevo dataset vacío"""
    if not name.endswith('.txt'):
        name = name + '.txt'
    
    # Limpiar el nombre del archivo
    import re
    safe_name = re.sub(r'[^\w\-_\.]', '_', name)
    
    file_path = DATA_DIR / safe_name
    
    if file_path.exists():
        raise HTTPException(status_code=400, detail="El dataset ya existe")
    
    # Crear archivo vacío
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el dataset: {str(e)}")
    
    return {
        "success": True,
        "message": f"Dataset {safe_name} creado",
        "filename": safe_name
    }


@router.delete("/api/datasets/{filename}")
async def delete_dataset(filename: str):
    """Elimina un dataset"""
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    if file_path.name == "poems.txt":  # Proteger el dataset principal
        raise HTTPException(status_code=400, detail="No se puede eliminar el dataset principal")
    
    file_path.unlink()
    
    return {"success": True, "message": f"Dataset {filename} eliminado"}


@router.get("/api/models")
async def list_models():
    """Lista todos los modelos entrenados"""
    models = []
    
    if not MODELS_DIR.exists():
        return {"models": []}
    
    for model_dir in MODELS_DIR.iterdir():
        if model_dir.is_dir():
            config_path = model_dir / "config.json"
            if config_path.exists():
                try:
                    stat = model_dir.stat()
                    # Calcular tamaño del modelo
                    total_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                    
                    models.append({
                        "name": model_dir.name,
                        "path": str(model_dir),
                        "size": total_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except Exception as e:
                    print(f"Error al leer modelo {model_dir}: {e}")
    
    return {"models": models}


@router.post("/api/train")
async def start_training(request: TrainingRequest):
    """Inicia el entrenamiento de un modelo"""
    # Verificar que el archivo existe
    poems_file = Path(request.poems_file)
    if not poems_file.exists():
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {request.poems_file}")
    
    # Verificar que no hay un entrenamiento en curso
    training_status_file = MODELS_DIR / ".training_status.json"
    if training_status_file.exists():
        with open(training_status_file, 'r') as f:
            status = json.load(f)
            if status.get("status") == "training":
                raise HTTPException(status_code=400, detail="Ya hay un entrenamiento en curso")
    
    # Iniciar entrenamiento en background (usar threading o asyncio)
    import threading
    
    def train_model():
        try:
            # Actualizar estado
            status = {
                "status": "training",
                "started_at": datetime.now().isoformat(),
                "poems_file": request.poems_file,
                "output_dir": request.output_dir
            }
            with open(training_status_file, 'w') as f:
                json.dump(status, f)
            
            # Entrenar
            trainer = PoetryTrainer(
                base_model=request.base_model,
                output_dir=request.output_dir
            )
            trainer.train_from_file(
                poems_file=str(poems_file),
                num_epochs=request.epochs,
                batch_size=request.batch_size,
                learning_rate=request.learning_rate
            )
            
            # Actualizar estado a completado
            status["status"] = "completed"
            status["completed_at"] = datetime.now().isoformat()
            with open(training_status_file, 'w') as f:
                json.dump(status, f)
        except Exception as e:
            # Actualizar estado a error
            status = {
                "status": "error",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }
            with open(training_status_file, 'w') as f:
                json.dump(status, f)
    
    # Iniciar en thread separado
    thread = threading.Thread(target=train_model, daemon=True)
    thread.start()
    
    return {
        "success": True,
        "message": "Entrenamiento iniciado",
        "training_id": "current"
    }


@router.get("/api/training/status")
async def get_training_status():
    """Obtiene el estado del entrenamiento actual"""
    training_status_file = MODELS_DIR / ".training_status.json"
    
    if not training_status_file.exists():
        return {"status": "idle", "message": "No hay entrenamiento en curso"}
    
    with open(training_status_file, 'r') as f:
        status = json.load(f)
    
    return status


@router.post("/api/training/cancel")
async def cancel_training():
    """Cancela el entrenamiento actual"""
    training_status_file = MODELS_DIR / ".training_status.json"
    
    if not training_status_file.exists():
        raise HTTPException(status_code=400, detail="No hay entrenamiento en curso")
    
    # Marcar como cancelado (el entrenamiento debería verificar esto periódicamente)
    with open(training_status_file, 'r') as f:
        status = json.load(f)
    
    status["status"] = "cancelled"
    status["cancelled_at"] = datetime.now().isoformat()
    
    with open(training_status_file, 'w') as f:
        json.dump(status, f)
    
    return {"success": True, "message": "Entrenamiento cancelado"}


@router.delete("/api/models/{model_name}")
async def delete_model(model_name: str):
    """Elimina un modelo entrenado"""
    model_path = MODELS_DIR / model_name
    
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    
    # Proteger el modelo principal
    if model_name == "poetry_model":
        raise HTTPException(status_code=400, detail="No se puede eliminar el modelo principal")
    
    shutil.rmtree(model_path)
    
    return {"success": True, "message": f"Modelo {model_name} eliminado"}


@router.get("/api/stats")
async def get_stats():
    """Obtiene estadísticas del sistema"""
    stats = {
        "datasets": {
            "count": len(list(DATA_DIR.glob("*.txt"))),
            "total_size": sum(f.stat().st_size for f in DATA_DIR.glob("*.txt"))
        },
        "models": {
            "count": len([d for d in MODELS_DIR.iterdir() if d.is_dir() and (d / "config.json").exists()]),
            "total_size": sum(
                sum(f.stat().st_size for f in d.rglob('*') if f.is_file())
                for d in MODELS_DIR.iterdir()
                if d.is_dir()
            )
        },
        "epub_files": {
            "count": len(list(EPUB_DIR.glob("*.epub"))),
            "total_size": sum(f.stat().st_size for f in EPUB_DIR.glob("*.epub"))
        }
    }
    
    return stats

