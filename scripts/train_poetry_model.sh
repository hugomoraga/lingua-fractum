#!/bin/bash
# Script para entrenar un modelo de poesía desde archivos EPUB

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Entrenamiento de Modelo de Poesía${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Directorios
EPUB_DIR="${1:-data/epub}"
POEMS_FILE="${2:-data/poems.txt}"
MODEL_DIR="${3:-models/poetry_model}"

echo -e "${YELLOW}Configuración:${NC}"
echo "  Directorio EPUB: $EPUB_DIR"
echo "  Archivo de poesías: $POEMS_FILE"
echo "  Modelo de salida: $MODEL_DIR"
echo ""

# Paso 1: Extraer poesías de EPUBs
if [ -d "$EPUB_DIR" ] && [ "$(ls -A $EPUB_DIR/*.epub 2>/dev/null)" ]; then
    echo -e "${GREEN}[1/2]${NC} Extrayendo poesías de archivos EPUB..."
    poetry run python -m poema_algoritmo.epub_processor "$EPUB_DIR" -o "$POEMS_FILE"
    echo ""
else
    echo -e "${YELLOW}⚠${NC} No se encontraron archivos EPUB en $EPUB_DIR"
    echo "  Usando archivo de poesías existente: $POEMS_FILE"
    echo ""
fi

# Verificar que existe el archivo de poesías
if [ ! -f "$POEMS_FILE" ]; then
    echo -e "${YELLOW}Error:${NC} No se encontró el archivo de poesías: $POEMS_FILE"
    echo "  Por favor, proporciona archivos EPUB o un archivo de poesías válido"
    exit 1
fi

# Paso 2: Entrenar modelo
echo -e "${GREEN}[2/2]${NC} Entrenando modelo..."
echo ""
poetry run python -m poema_algoritmo.train_model "$POEMS_FILE" \
    -o "$MODEL_DIR" \
    -e 3 \
    --batch-size 4 \
    --learning-rate 5e-5

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Entrenamiento completado!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Para usar el modelo entrenado, ejecuta:"
echo "  TRAINED_MODEL_PATH=$MODEL_DIR poetry run uvicorn poema_algoritmo.main:app --reload"
echo ""

