from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
import os

class PoemGenerator:
    """Generador de poemas usando modelos de lenguaje"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()
    
    def _load_model(self):
        """Cargar el modelo de generación de texto"""
        # Verificar si hay una variable de entorno para usar solo modelos locales
        use_local_only = os.getenv("USE_LOCAL_MODELS_ONLY", "false").lower() == "true"
        
        # Verificar si hay un modelo entrenado localmente
        trained_model_path = os.getenv("TRAINED_MODEL_PATH", "models/poetry_model")
        
        try:
            # PRIMERO: Intentar cargar modelo entrenado localmente (si existe)
            if os.path.exists(trained_model_path) and os.path.exists(
                os.path.join(trained_model_path, "config.json")
            ):
                try:
                    print(f"Intentando cargar modelo entrenado desde: {trained_model_path}")
                    self.tokenizer = GPT2Tokenizer.from_pretrained(trained_model_path)
                    self.model = GPT2LMHeadModel.from_pretrained(trained_model_path)
                    self.model.to(self.device)
                    self.model.eval()
                    
                    if self.tokenizer.pad_token is None:
                        self.tokenizer.pad_token = self.tokenizer.eos_token
                    
                    print(f"✓ Modelo entrenado cargado desde: {trained_model_path}")
                    return
                except Exception as e:
                    print(f"  Error al cargar modelo entrenado: {e}")
                    print("  Intentando con modelos pre-entrenados...")
            
            # SEGUNDO: Intentar cargar modelos pre-entrenados
            cache_dir = os.path.expanduser("~/.cache/huggingface/transformers")
            
            # Lista de modelos a intentar (en orden de preferencia)
            models_to_try = [
                "datasets/gpt2-spanish",
                "DeepESP/gpt2-spanish",
                "gpt2"
            ]
            
            for model_name in models_to_try:
                try:
                    # Si solo queremos modelos locales, verificar que existan en caché
                    if use_local_only:
                        # Verificar si el modelo está en caché
                        model_path = os.path.join(cache_dir, model_name.replace("/", "--"))
                        if not os.path.exists(model_path):
                            print(f"Modelo {model_name} no encontrado en caché local, saltando...")
                            continue
                    
                    # Intentar cargar el modelo (desde caché si existe, o descargar si no)
                    self.tokenizer = GPT2Tokenizer.from_pretrained(
                        model_name,
                        local_files_only=use_local_only
                    )
                    self.model = GPT2LMHeadModel.from_pretrained(
                        model_name,
                        local_files_only=use_local_only
                    )
                    self.model.to(self.device)
                    self.model.eval()
                    
                    # Configurar tokenizer
                    if self.tokenizer.pad_token is None:
                        self.tokenizer.pad_token = self.tokenizer.eos_token
                    
                    print(f"✓ Modelo cargado: {model_name}")
                    if use_local_only:
                        print("  (modo solo-local activado)")
                    return
                    
                except Exception as e:
                    if use_local_only:
                        print(f"  Modelo {model_name} no disponible localmente")
                    continue
            
            # Si llegamos aquí, no se pudo cargar ningún modelo
            if use_local_only:
                print("⚠ No se encontraron modelos locales. Usando generación básica.")
            else:
                print("⚠ Error al cargar modelos. Usando generación básica.")
            self.model = None
            
        except Exception as e:
            print(f"Error al cargar el modelo: {e}")
            print("Usando generación básica como fallback")
            self.model = None
    
    def generate(self, prompt: str, max_length: int = 200, temperature: float = 0.9) -> str:
        """Generar un poema basado en el prompt"""
        
        if self.model is None:
            # Fallback: generación básica con plantilla
            return self._generate_fallback(prompt)
        
        try:
            # Preparar el prompt
            prompt_text = f"Poema sobre {prompt}:\n\n"
            
            # Tokenizar
            inputs = self.tokenizer.encode(prompt_text, return_tensors="pt")
            inputs = inputs.to(self.device)
            
            # Generar
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.95,
                    top_k=50,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1
                )
            
            # Decodificar
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extraer solo el poema generado (sin el prompt)
            poem = generated_text.replace(prompt_text, "").strip()
            
            # Limpiar y formatear
            poem = self._format_poem(poem)
            
            return poem
            
        except Exception as e:
            print(f"Error en la generación: {e}")
            return self._generate_fallback(prompt)
    
    def _generate_fallback(self, prompt: str) -> str:
        """Generación básica cuando no hay modelo disponible"""
        # Plantillas de poemas básicos
        templates = [
            f"""Sobre {prompt} escribo,
con palabras que fluyen,
como río que va,
hacia el mar del pensamiento.

En {prompt} encuentro,
la esencia de la vida,
un susurro en el viento,
una historia contada.""",
            
            f"""{prompt.capitalize()} es
un susurro en la noche,
una luz en la oscuridad,
un canto en el silencio.

{prompt.capitalize()} me lleva
a lugares desconocidos,
donde las palabras bailan,
y los versos cobran vida.""",
            
            f"""En el eco de {prompt},
resuena la poesía,
cada palabra un latido,
cada verso una melodía.

{prompt.capitalize()} transforma
lo común en extraordinario,
lo simple en profundo,
lo efímero en eterno."""
        ]
        
        import random
        return random.choice(templates)
    
    def _format_poem(self, text: str) -> str:
        """Formatear el poema generado"""
        # Dividir en líneas y limpiar
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:
                formatted_lines.append(line)
        
        # Si hay muy pocas líneas, intentar dividir por puntos
        if len(formatted_lines) < 3:
            sentences = text.split('.')
            formatted_lines = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        return '\n'.join(formatted_lines[:20])  # Limitar a 20 líneas

