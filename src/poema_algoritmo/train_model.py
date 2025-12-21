"""
Script para entrenar un modelo de generación de poesía
"""
import os
import re
import torch
from transformers import (
    GPT2LMHeadModel,
    GPT2Tokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from typing import List, Optional


class PoetryTrainer:
    """Entrenador de modelos para generación de poesía"""
    
    def __init__(
        self,
        base_model: str = None,
        output_dir: str = "models/poetry_model",
        max_length: int = 512
    ):
        self.output_dir = output_dir
        self.max_length = max_length
        
        # Si no se especifica modelo base, intentar cargar uno en español primero
        if base_model is None:
            base_model = self._get_best_spanish_model()
        
        self.base_model = base_model
        
        # Cargar modelo y tokenizer base
        print(f"Cargando modelo base: {base_model}")
        self.tokenizer = GPT2Tokenizer.from_pretrained(base_model)
        self.model = GPT2LMHeadModel.from_pretrained(base_model)
        
        # Configurar tokenizer
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Aumentar tamaño del vocabulario si es necesario
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        
        print(f"✓ Modelo cargado. Vocabulario: {len(self.tokenizer)} tokens")
    
    def _get_best_spanish_model(self) -> str:
        """
        Intenta encontrar el mejor modelo base en español disponible.
        Si no encuentra ninguno, usa GPT2 como fallback.
        """
        spanish_models = [
            "DeepESP/gpt2-spanish",
            "datasets/gpt2-spanish",
        ]
        
        for model_name in spanish_models:
            try:
                # Intentar cargar el tokenizer para verificar si existe
                tokenizer = GPT2Tokenizer.from_pretrained(model_name)
                print(f"✓ Modelo en español encontrado: {model_name}")
                return model_name
            except Exception:
                continue
        
        print("⚠ No se encontró modelo en español. Usando GPT2 (inglés) como base.")
        print("  Nota: Para mejores resultados, considera usar un modelo base en español.")
        return "gpt2"
    
    def load_poems_from_file(self, file_path: str) -> List[str]:
        """
        Carga poesías desde un archivo de texto
        Soporta múltiples formatos automáticamente
        
        Args:
            file_path: Ruta al archivo con poesías
            
        Returns:
            Lista de poesías
        """
        poems = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Detectar formato: ¿tiene separadores con ===?
        has_separators = '===' in content
        
        if has_separators:
            # Formato con separadores === POEMA X ===
            poem_blocks = re.split(r'={3,}', content)
            
            for block in poem_blocks:
                block = block.strip()
                # Eliminar encabezados como "=== POEMA 1 ==="
                lines = block.split('\n')
                poem_lines = [line for line in lines if not line.startswith('===') and line.strip()]
                
                if poem_lines:
                    poem = '\n'.join(poem_lines).strip()
                    if len(poem) > 50:
                        poems.append(poem)
        else:
            # Formato libre: detectar poemas por estructura
            poems = self._extract_poems_from_free_format(content)
        
        print(f"✓ Cargadas {len(poems)} poesías desde {file_path}")
        return poems
    
    def _extract_poems_from_free_format(self, content: str) -> List[str]:
        """
        Extrae poemas de un formato libre (sin separadores explícitos)
        Agrupa correctamente todas las líneas de cada poema
        
        Args:
            content: Contenido completo del archivo
            
        Returns:
            Lista de poemas extraídos
        """
        poems = []
        
        # Detectar y saltar prólogos/prefacios
        lines = content.split('\n')
        
        # Buscar donde terminan los metadatos
        start_idx = 0
        for i, line in enumerate(lines[:100]):
            line_upper = line.strip().upper()
            if any(keyword in line_upper for keyword in ['AL LECTOR', 'SPLEEN', 'BENDICIÓN', 'EL ALBATROS']):
                start_idx = i
                break
        
        if start_idx > 0:
            lines = lines[start_idx:]
        
        current_poem_lines = []
        current_poem_title = None
        empty_line_count = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Detectar títulos (líneas en mayúsculas, cortas, solas)
            is_title = (
                line and
                len(line) < 100 and 
                line.isupper() and 
                not line.endswith(',') and
                not line.endswith('.') and
                not line.endswith(';') and
                not line.endswith(':') and
                len(line.split()) < 15 and
                not re.match(r'^\d{4}', line)  # No años
            )
            
            # Detectar metadatos
            is_metadata = self._is_metadata_line(line) if line else False
            
            # Detectar años solos (ej: "1844 (?)")
            is_year = re.match(r'^\d{4}\s*[\(\)\?]*\s*$', line) if line else False
            
            if is_title and not is_metadata:
                # Nuevo título encontrado: guardar poema anterior si existe
                if current_poem_lines and len(current_poem_lines) >= 3:
                    poem = '\n'.join(current_poem_lines).strip()
                    if self._is_valid_poem(poem):
                        poems.append(poem)
                
                # Iniciar nuevo poema
                current_poem_title = line
                current_poem_lines = []
                empty_line_count = 0
                i += 1
                continue
            
            elif is_year or is_metadata:
                # Año o metadata: ignorar y continuar
                i += 1
                continue
            
            elif not line:
                # Línea vacía
                empty_line_count += 1
                
                # Si hay muchas líneas vacías consecutivas (3+), verificar si es fin de poema
                if empty_line_count >= 3:
                    # Mirar adelante para ver si hay un año o título (fin de poema)
                    # o si continúa el contenido (parte del poema)
                    look_ahead = 5
                    found_year_or_title = False
                    
                    for j in range(i + 1, min(i + 1 + look_ahead, len(lines))):
                        next_line = lines[j].strip()
                        if not next_line:
                            continue
                        
                        # Verificar si es año o título
                        is_next_year = re.match(r'^\d{4}\s*[\(\)\?]*\s*$', next_line)
                        is_next_title = (
                            next_line and
                            len(next_line) < 100 and 
                            next_line.isupper() and 
                            not next_line.endswith(',') and
                            not next_line.endswith('.') and
                            not next_line.endswith(';') and
                            not next_line.endswith(':') and
                            len(next_line.split()) < 15 and
                            not re.match(r'^\d{4}', next_line) and
                            not self._is_metadata_line(next_line)
                        )
                        
                        if is_next_year or is_next_title:
                            found_year_or_title = True
                            break
                        
                        # Si encontramos contenido de poema, no es el fin
                        if next_line and not self._is_metadata_line(next_line):
                            # Es contenido, no cerrar el poema
                            found_year_or_title = False
                            break
                    
                    # Solo cerrar si encontramos año o título adelante
                    if found_year_or_title:
                        # Guardar poema actual si tiene contenido
                        if current_poem_lines and len(current_poem_lines) >= 3:
                            poem = '\n'.join(current_poem_lines).strip()
                            if self._is_valid_poem(poem):
                                poems.append(poem)
                        current_poem_lines = []
                        current_poem_title = None
                        empty_line_count = 0
                    # Si no, es parte del poema (muchas líneas vacías entre estrofas)
                    elif current_poem_lines:
                        # Agregar líneas vacías para preservar estructura
                        for _ in range(min(empty_line_count, 2)):
                            current_poem_lines.append('')
                        empty_line_count = 0
                # Si es solo 1-2 líneas vacías, es parte del poema (separador de estrofa)
                elif empty_line_count <= 2 and current_poem_lines:
                    # Agregar línea vacía para preservar estructura
                    current_poem_lines.append('')
                i += 1
                continue
            
            else:
                # Línea de contenido: agregar al poema actual
                empty_line_count = 0
                current_poem_lines.append(line)
                i += 1
        
        # Guardar último poema si existe
        if current_poem_lines and len(current_poem_lines) >= 3:
            poem = '\n'.join(current_poem_lines).strip()
            if self._is_valid_poem(poem):
                poems.append(poem)
        
        # Eliminar duplicados y limpiar
        unique_poems = []
        seen = set()
        for poem in poems:
            # Normalizar para comparación
            poem_normalized = re.sub(r'\s+', ' ', poem.lower())[:300]
            if poem_normalized not in seen:
                seen.add(poem_normalized)
                unique_poems.append(poem)
        
        return unique_poems
    
    def _is_metadata_line(self, line: str) -> bool:
        """Detecta si una línea es metadatos"""
        line_lower = line.lower()
        metadata_patterns = [
            r'^(prólogo|prologo|prefacio|preface|dedicatoria|dedication)',
            r'^(traductor|translator|autor|author|editor|publisher)',
            r'^\d{4}\s*\.?\s*$',  # Años solos
            r'^(parte|part|capítulo|chapter)\s+\d+',
            r'^(índice|index|tabla de contenidos)',
            r'^al (lector|reader)',
            r'^(con los sentimientos|dedico|dedica)',
            r'^(charles|baudelaire|neruda|whitman|rilke|rimbaud)',
        ]
        for pattern in metadata_patterns:
            if re.match(pattern, line_lower):
                return True
        return False
    
    def _is_valid_poem(self, poem: str) -> bool:
        """Valida si un texto es un poema válido"""
        if len(poem) < 50:  # Muy corto
            return False
        
        if len(poem) > 5000:  # Muy largo (probablemente prosa)
            return False
        
        lines = poem.split('\n')
        if len(lines) < 3:  # Muy pocas líneas
            return False
        
        # Calcular estadísticas
        line_lengths = [len(line.strip()) for line in lines if line.strip()]
        if not line_lengths:
            return False
        
        avg_length = sum(line_lengths) / len(line_lengths)
        
        # Si el promedio es muy largo, probablemente es prosa
        if avg_length > 150:
            return False
        
        # Debe tener al menos algunas líneas cortas (característica de poesía)
        short_lines = [l for l in line_lengths if l < 100]
        if len(short_lines) < len(line_lengths) * 0.3:  # Menos del 30% son cortas
            return False
        
        return True
    
    def prepare_dataset(self, poems: List[str], include_directives: bool = True) -> Dataset:
        """
        Prepara el dataset para entrenamiento
        
        Args:
            poems: Lista de poesías
            include_directives: Si True, agrega formato con directrices para entrenar al modelo
                               a seguir instrucciones
            
        Returns:
            Dataset preparado
        """
        print("Preparando dataset...")
        
        # Si include_directives, crear ejemplos con formato de directrices
        if include_directives:
            from .poetry_agent import PoetryAgent
            import random
            agent = PoetryAgent()
            formatted_poems = []
            
            print("  Agregando formato con directrices para entrenar seguimiento de instrucciones...")
            
            # Palabras clave comunes en poesía para detectar temas
            emotion_keywords = ['triste', 'alegre', 'melancólico', 'nostálgico', 'amoroso', 'oscuro', 'sereno']
            style_keywords = ['soneto', 'haiku', 'verso libre', 'romántico', 'moderno']
            
            for poem in poems:
                # Extraer conceptos y características del poema
                lines = poem.split('\n')
                poem_lower = poem.lower()
                
                # Detectar concepto principal (primeras palabras significativas)
                first_line = lines[0].strip() if lines else ""
                concept = None
                
                # Estrategia 1: Si la primera línea es corta, es probablemente un título/concepto
                if first_line and len(first_line.split()) <= 5 and len(first_line) < 50:
                    concept = first_line
                else:
                    # Estrategia 2: Extraer palabras clave del poema
                    words = poem.split()[:5]
                    # Filtrar palabras comunes
                    stop_words = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'y', 'que', 'a'}
                    meaningful_words = [w for w in words if w.lower() not in stop_words and len(w) > 3]
                    if meaningful_words:
                        concept = ' '.join(meaningful_words[:2])  # Tomar 1-2 palabras significativas
                
                if not concept:
                    # Fallback: usar primeras palabras
                    words = poem.split()[:3]
                    concept = ' '.join(words) if words else "poesía"
                
                # Detectar características del poema
                detected_emotion = None
                detected_style = None
                
                for emotion in emotion_keywords:
                    if emotion in poem_lower:
                        detected_emotion = emotion
                        break
                
                for style in style_keywords:
                    if style in poem_lower:
                        detected_style = style
                        break
                
                # Crear múltiples variantes de formato de instrucción
                variants = []
                
                # Variante 1: Simple
                variants.append(f"Tema: {concept}\n\nPoema sobre {concept}:\n\n{poem}")
                
                # Variante 2: Con instrucción explícita
                variants.append(f"Escribe un poema sobre {concept}:\n\n{poem}")
                
                # Variante 3: Con formato estructurado
                if detected_emotion:
                    variants.append(f"Tema: {concept}\nTono: {detected_emotion}\n\nPoema sobre {concept}:\n\n{poem}")
                
                if detected_style:
                    variants.append(f"Tema: {concept}\nEstilo: {detected_style}\n\nPoema sobre {concept}:\n\n{poem}")
                
                # Variante 4: Instrucción en lenguaje natural
                instruction = f"escribe un poema sobre {concept}"
                if detected_emotion:
                    instruction += f" {detected_emotion}"
                variants.append(f"Instrucción: {instruction}\n\nPoema:\n\n{poem}")
                
                # Seleccionar una variante aleatoria
                formatted_poems.append(random.choice(variants))
            
            # Mezclar: 80% con directrices, 20% sin directrices (para mantener flexibilidad)
            mixed_poems = []
            for i, poem in enumerate(poems):
                if i < len(formatted_poems):
                    # 80% con formato de instrucciones, 20% sin formato
                    if random.random() < 0.8:
                        mixed_poems.append(formatted_poems[i])
                    else:
                        mixed_poems.append(poem)
                else:
                    mixed_poems.append(poem)
            
            poems = mixed_poems
            print(f"  ✓ Dataset preparado con formato de instrucciones (80% con formato, 20% sin formato)")
            print(f"  ✓ Variantes de formato: simple, estructurado, lenguaje natural")
        
        # Tokenizar todas las poesías
        def tokenize_function(examples):
            # Agregar token de fin de texto al final de cada poema
            texts = [poem + self.tokenizer.eos_token for poem in examples['text']]
            
            # Tokenizar
            tokenized = self.tokenizer(
                texts,
                truncation=True,
                max_length=self.max_length,
                padding='max_length',
                return_tensors='pt'
            )
            
            # Los labels son iguales a los input_ids (para language modeling)
            tokenized['labels'] = tokenized['input_ids'].clone()
            
            return tokenized
        
        # Crear dataset
        dataset_dict = {'text': poems}
        dataset = Dataset.from_dict(dataset_dict)
        
        # Tokenizar
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=['text']
        )
        
        print(f"✓ Dataset preparado: {len(tokenized_dataset)} ejemplos")
        return tokenized_dataset
    
    def train(
        self,
        dataset: Dataset,
        num_epochs: int = 5,
        batch_size: int = 4,
        learning_rate: float = 5e-5,
        save_steps: int = 500,
        eval_steps: Optional[int] = None
    ):
        """
        Entrena el modelo
        
        Args:
            dataset: Dataset preparado
            num_epochs: Número de épocas
            batch_size: Tamaño del batch
            learning_rate: Tasa de aprendizaje
            save_steps: Guardar cada N pasos
            eval_steps: Evaluar cada N pasos (opcional)
        """
        print(f"\n{'='*60}")
        print("INICIANDO ENTRENAMIENTO")
        print(f"{'='*60}")
        print(f"Épocas: {num_epochs}")
        print(f"Batch size: {batch_size}")
        print(f"Learning rate: {learning_rate}")
        print(f"Ejemplos: {len(dataset)}")
        print(f"{'='*60}\n")
        
        # Crear directorio de salida
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configurar argumentos de entrenamiento
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            overwrite_output_dir=True,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_steps=100,
            logging_steps=50,
            save_steps=save_steps,
            eval_steps=eval_steps,
            save_total_limit=3,
            prediction_loss_only=True,
            remove_unused_columns=False,
            fp16=torch.cuda.is_available(),  # Usar FP16 si hay GPU
            dataloader_pin_memory=False,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # No masked language modeling, solo causal LM
        )
        
        # Crear trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=dataset,
        )
        
        # Entrenar
        print("Iniciando entrenamiento...")
        trainer.train()
        
        # Guardar modelo final
        print(f"\nGuardando modelo en {self.output_dir}...")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)
        
        print(f"\n✓ Entrenamiento completado!")
        print(f"✓ Modelo guardado en: {self.output_dir}")
    
    def train_from_file(
        self,
        poems_file: str,
        num_epochs: int = 5,
        batch_size: int = 4,
        learning_rate: float = 5e-5
    ):
        """
        Entrena desde un archivo de poesías (método de conveniencia)
        
        Args:
            poems_file: Archivo con poesías (puede ser una lista de archivos separados por comas)
            num_epochs: Número de épocas
            batch_size: Tamaño del batch
            learning_rate: Tasa de aprendizaje
        """
        # Si hay múltiples archivos separados por comas, combinarlos
        if ',' in poems_file:
            file_list = [f.strip() for f in poems_file.split(',')]
            print(f"Cargando poemas de {len(file_list)} archivos...")
            all_poems = []
            for file_path in file_list:
                if os.path.exists(file_path):
                    poems = self.load_poems_from_file(file_path)
                    all_poems.extend(poems)
                    print(f"  ✓ {len(poems)} poemas de {file_path}")
                else:
                    print(f"  ⚠ Archivo no encontrado: {file_path}")
            poems = all_poems
        else:
            poems = self.load_poems_from_file(poems_file)
        
        if len(poems) < 10:
            print("⚠ Advertencia: Muy pocas poesías. Se recomiendan al menos 50-100 para un buen entrenamiento.")
        elif len(poems) < 50:
            print("⚠ Advertencia: Pocas poesías. Se recomiendan al menos 100-200 para mejor calidad.")
        else:
            print(f"✓ Dataset con {len(poems)} poemas - tamaño adecuado")
        
        dataset = self.prepare_dataset(poems)
        self.train(dataset, num_epochs, batch_size, learning_rate)


def main():
    """Función principal para entrenar desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Entrenar modelo de poesía')
    parser.add_argument('poems_file', help='Archivo con poesías (formato texto)')
    parser.add_argument('-o', '--output', default='models/poetry_model',
                       help='Directorio de salida (default: models/poetry_model)')
    parser.add_argument('-b', '--base-model', default=None,
                       help='Modelo base (default: intenta usar modelo en español, luego gpt2)')
    parser.add_argument('-e', '--epochs', type=int, default=5,
                       help='Número de épocas (default: 5, recomendado: 5-10 para mejor calidad)')
    parser.add_argument('--batch-size', type=int, default=4,
                       help='Tamaño del batch (default: 4)')
    parser.add_argument('--learning-rate', type=float, default=5e-5,
                       help='Tasa de aprendizaje (default: 5e-5)')
    parser.add_argument('--max-length', type=int, default=512,
                       help='Longitud máxima de secuencia (default: 512)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.poems_file):
        print(f"Error: El archivo {args.poems_file} no existe")
        return
    
    trainer = PoetryTrainer(
        base_model=args.base_model,
        output_dir=args.output,
        max_length=args.max_length
    )
    
    trainer.train_from_file(
        poems_file=args.poems_file,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )


if __name__ == "__main__":
    main()

