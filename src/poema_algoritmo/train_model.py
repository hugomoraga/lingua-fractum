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
        base_model: str = "gpt2",
        output_dir: str = "models/poetry_model",
        max_length: int = 512
    ):
        self.base_model = base_model
        self.output_dir = output_dir
        self.max_length = max_length
        
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
    
    def load_poems_from_file(self, file_path: str) -> List[str]:
        """
        Carga poesías desde un archivo de texto
        
        Args:
            file_path: Ruta al archivo con poesías
            
        Returns:
            Lista de poesías
        """
        poems = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Dividir por separadores de poemas
            poem_blocks = re.split(r'={3,}', content)
            
            for block in poem_blocks:
                block = block.strip()
                # Eliminar encabezados como "=== POEMA 1 ==="
                lines = block.split('\n')
                poem_lines = [line for line in lines if not line.startswith('===') and line.strip()]
                
                if poem_lines:
                    poem = '\n'.join(poem_lines).strip()
                    if len(poem) > 50:  # Filtrar poemas muy cortos
                        poems.append(poem)
        
        print(f"✓ Cargadas {len(poems)} poesías desde {file_path}")
        return poems
    
    def prepare_dataset(self, poems: List[str]) -> Dataset:
        """
        Prepara el dataset para entrenamiento
        
        Args:
            poems: Lista de poesías
            
        Returns:
            Dataset preparado
        """
        print("Preparando dataset...")
        
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
        num_epochs: int = 3,
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
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 5e-5
    ):
        """
        Entrena desde un archivo de poesías (método de conveniencia)
        
        Args:
            poems_file: Archivo con poesías
            num_epochs: Número de épocas
            batch_size: Tamaño del batch
            learning_rate: Tasa de aprendizaje
        """
        poems = self.load_poems_from_file(poems_file)
        
        if len(poems) < 10:
            print("⚠ Advertencia: Muy pocas poesías. Se recomiendan al menos 50-100 para un buen entrenamiento.")
        
        dataset = self.prepare_dataset(poems)
        self.train(dataset, num_epochs, batch_size, learning_rate)


def main():
    """Función principal para entrenar desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Entrenar modelo de poesía')
    parser.add_argument('poems_file', help='Archivo con poesías (formato texto)')
    parser.add_argument('-o', '--output', default='models/poetry_model',
                       help='Directorio de salida (default: models/poetry_model)')
    parser.add_argument('-b', '--base-model', default='gpt2',
                       help='Modelo base (default: gpt2)')
    parser.add_argument('-e', '--epochs', type=int, default=3,
                       help='Número de épocas (default: 3)')
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

