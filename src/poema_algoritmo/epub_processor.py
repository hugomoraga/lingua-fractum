"""
Procesador de archivos EPUB para extraer poesías
"""
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import os
from typing import List, Optional


class EPUBProcessor:
    """Procesa archivos EPUB para extraer poesías"""
    
    def __init__(self):
        self.poems = []
    
    def extract_text_from_epub(self, epub_path: str) -> List[str]:
        """
        Extrae todo el texto de un archivo EPUB
        
        Args:
            epub_path: Ruta al archivo EPUB
            
        Returns:
            Lista de strings con el contenido de cada capítulo/sección
        """
        try:
            book = epub.read_epub(epub_path)
            chapters = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    try:
                        # Parsear el contenido HTML
                        content = item.get_content()
                        if content:
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            # Extraer texto preservando saltos de línea
                            # Eliminar scripts y estilos
                            for script in soup(["script", "style"]):
                                script.decompose()
                            
                            # Obtener texto preservando estructura
                            text = soup.get_text(separator='\n')
                            
                            # Limpiar el texto (más permisivo)
                            text = self._clean_text(text)
                            if text and len(text.strip()) > 30:  # Filtrar textos muy cortos
                                chapters.append(text)
                    except Exception as e:
                        print(f"  Advertencia: Error al procesar un documento: {e}")
                        continue
            
            return chapters
            
        except Exception as e:
            print(f"Error al procesar EPUB {epub_path}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_poems_from_text(self, text: str) -> List[str]:
        """
        Extrae poesías de un texto basándose en patrones comunes
        
        Args:
            text: Texto a procesar
            
        Returns:
            Lista de poesías extraídas
        """
        poems = []
        
        # PRIMERO: Detectar si hay separadores explícitos === POEMA === o === POEMA X ===
        separator_pattern = r'===+\s*POEMA\s+\d+\s*===+|===+\s*POEMA\s*===+'
        if re.search(separator_pattern, text, re.IGNORECASE):
            # Dividir por separadores explícitos
            parts = re.split(separator_pattern, text, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Limpiar el poema
                cleaned_poem = self._clean_poem(part)
                if cleaned_poem and len(cleaned_poem) > 30:
                    poems.append(cleaned_poem)
            
            # Si encontramos poemas con separadores, retornarlos (ya limpios y únicos)
            if poems:
                # Eliminar duplicados
                unique_poems = []
                seen = set()
                for poem in poems:
                    poem_hash = hash(poem[:100])  # Primeros 100 caracteres
                    if poem_hash not in seen:
                        seen.add(poem_hash)
                        unique_poems.append(poem)
                return unique_poems
        
        # SEGUNDO: Si no hay separadores, usar lógica de detección por estructura
        # Dividir por líneas vacías dobles o más (párrafos/poemas)
        paragraphs = re.split(r'\n\s*\n+', text)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Dividir en líneas
            lines = [line.strip() for line in para.split('\n') if line.strip()]
            
            # Filtrar líneas muy largas que probablemente son prosa
            valid_lines = []
            for line in lines:
                # Si una línea es muy larga (más de 150 caracteres), probablemente es prosa
                if len(line) > 150:
                    # Si hay líneas válidas antes, guardarlas como poema
                    if len(valid_lines) >= 3:
                        poem = '\n'.join(valid_lines)
                        if len(poem) > 30:
                            poems.append(poem)
                    valid_lines = []
                else:
                    valid_lines.append(line)
            
            # Si quedaron líneas válidas al final
            if len(valid_lines) >= 3:
                poem = '\n'.join(valid_lines)
                if len(poem) > 30:
                    poems.append(poem)
            
            # También intentar detectar poemas por estructura (múltiples líneas cortas)
            if len(lines) >= 3:
                # Calcular estadísticas de las líneas
                line_lengths = [len(line) for line in lines]
                avg_length = sum(line_lengths) / len(line_lengths)
                max_length = max(line_lengths)
                
                # Criterios más flexibles para poesía:
                # - Al menos 3 líneas
                # - Línea promedio no muy larga (menos de 120 caracteres)
                # - No todas las líneas son muy largas
                if avg_length < 120 and max_length < 200:
                    poem = '\n'.join(lines)
                    # Filtrar si es demasiado corto o demasiado largo (probablemente prosa)
                    if 30 < len(poem) < 2000:
                        poems.append(poem)
        
        # Eliminar duplicados y limpiar
        unique_poems = []
        seen = set()
        for poem in poems:
            poem_clean = self._clean_poem(poem)
            # Usar hash para detectar duplicados similares
            poem_hash = hash(poem_clean[:100])  # Primeros 100 caracteres
            if poem_hash not in seen and len(poem_clean) > 30:
                seen.add(poem_hash)
                unique_poems.append(poem_clean)
        
        return unique_poems
    
    def process_epub_file(self, epub_path: str) -> List[str]:
        """
        Procesa un archivo EPUB completo y extrae todas las poesías
        
        Args:
            epub_path: Ruta al archivo EPUB
            
        Returns:
            Lista de poesías extraídas
        """
        print(f"Procesando: {epub_path}")
        chapters = self.extract_text_from_epub(epub_path)
        print(f"  Capítulos/secciones encontrados: {len(chapters)}")
        
        all_poems = []
        for i, chapter in enumerate(chapters, 1):
            poems = self.extract_poems_from_text(chapter)
            if poems:
                print(f"    Capítulo {i}: {len(poems)} poesías")
                all_poems.extend(poems)
        
        print(f"  ✓ Total extraídas: {len(all_poems)} poesías")
        return all_poems
    
    def process_directory(self, directory: str) -> List[str]:
        """
        Procesa todos los archivos EPUB en un directorio
        
        Args:
            directory: Directorio con archivos EPUB
            
        Returns:
            Lista de todas las poesías extraídas
        """
        all_poems = []
        epub_files = [f for f in os.listdir(directory) if f.endswith('.epub')]
        
        print(f"Encontrados {len(epub_files)} archivos EPUB")
        
        for epub_file in epub_files:
            epub_path = os.path.join(directory, epub_file)
            poems = self.process_epub_file(epub_path)
            all_poems.extend(poems)
        
        return all_poems
    
    def save_poems_to_file(self, poems: List[str], output_path: str):
        """
        Guarda las poesías en un archivo de texto
        
        Args:
            poems: Lista de poesías
            output_path: Ruta donde guardar el archivo
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, poem in enumerate(poems, 1):
                f.write(f"=== POEMA {i} ===\n\n")
                f.write(poem)
                f.write("\n\n" + "="*50 + "\n\n")
        
        print(f"✓ Guardadas {len(poems)} poesías en {output_path}")
    
    def _clean_text(self, text: str) -> str:
        """Limpia el texto extraído (más permisivo para preservar estructura)"""
        # Reemplazar tabs por espacios
        text = text.replace('\t', ' ')
        
        # Limpiar notas de pie de página (números entre corchetes como [59], [60])
        text = re.sub(r'\[\d+\]', '', text)
        
        # Limpiar referencias a notas al final de líneas o párrafos
        text = re.sub(r'\s*\[\d+\]\s*', ' ', text)
        
        # Normalizar espacios pero preservar saltos de línea
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Limpiar espacios múltiples en la línea pero mantenerla
            line = re.sub(r' +', ' ', line)
            line = line.strip()
            if line:
                # Filtrar líneas que son solo metadatos comunes
                if not self._is_metadata_line(line):
                    cleaned_lines.append(line)
        
        # Unir líneas preservando estructura
        text = '\n'.join(cleaned_lines)
        
        # Normalizar espacios múltiples entre líneas
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _is_metadata_line(self, line: str) -> bool:
        """Detecta si una línea es metadatos (títulos, autores, etc.)"""
        line_lower = line.lower()
        # Patrones comunes de metadatos
        metadata_patterns = [
            r'^(traductor|translator|autor|author|editor|publisher)',
            r'^\d{4}$',  # Años solos
            r'^(parte|part|capítulo|chapter)\s+\d+',
            r'^(dedicatoria|dedication|índice|index|tabla de contenidos)',
            r'^al (lector|reader)',
            r'^(con los sentimientos|dedico|dedica)',
        ]
        for pattern in metadata_patterns:
            if re.match(pattern, line_lower):
                return True
        # Líneas muy cortas que son probablemente títulos
        if len(line) < 30 and line.isupper():
            return True
        return False
    
    def _clean_poem(self, poem: str) -> str:
        """Limpia y formatea un poema"""
        # Eliminar líneas vacías múltiples
        lines = [line.strip() for line in poem.split('\n') if line.strip()]
        # Unir líneas manteniendo estructura
        cleaned = '\n'.join(lines)
        return cleaned


def main():
    """Función principal para procesar EPUBs desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extraer poesías de archivos EPUB')
    parser.add_argument('input', help='Archivo EPUB o directorio con EPUBs')
    parser.add_argument('-o', '--output', default='data/poems.txt', 
                       help='Archivo de salida (default: data/poems.txt)')
    
    args = parser.parse_args()
    
    processor = EPUBProcessor()
    
    if os.path.isfile(args.input):
        poems = processor.process_epub_file(args.input)
    elif os.path.isdir(args.input):
        poems = processor.process_directory(args.input)
    else:
        print(f"Error: {args.input} no es un archivo ni un directorio válido")
        return
    
    if poems:
        processor.save_poems_to_file(poems, args.output)
        print(f"\n✓ Total: {len(poems)} poesías extraídas")
    else:
        print("\n⚠ No se encontraron poesías en los archivos")

if __name__ == "__main__":
    main()

