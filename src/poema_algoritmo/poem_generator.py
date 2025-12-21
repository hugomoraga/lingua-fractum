from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
import os
from .poetry_agent import PoetryAgent
from .lm_studio_client import LMStudioClient

class PoemGenerator:
    """Generador de poemas usando modelos de lenguaje"""
    
    def __init__(self, use_lm_studio: bool = True):
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.agent = PoetryAgent(use_lm_studio=use_lm_studio)  # Agente para interpretar directrices
        
        # Cliente LM Studio para generación alternativa
        self.use_lm_studio = use_lm_studio
        self.lm_studio_client = None
        if use_lm_studio:
            lm_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
            self.lm_studio_client = LMStudioClient(base_url=lm_url)
            if self.lm_studio_client.is_available():
                print("✓ LM Studio disponible para generación de poesía")
            else:
                print("⚠ LM Studio no disponible, usando modelo local")
                self.lm_studio_client = None
        
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
    
    def generate(self, prompt: str, max_length: int = 200, temperature: float = 0.7, use_agent: bool = True, prefer_lm_studio: bool = True) -> tuple:
        """
        Generar un poema basado en el prompt
        
        Args:
            prompt: Input del usuario (puede ser concepto simple o directrices complejas)
            max_length: Longitud máxima del poema
            temperature: Temperatura para la generación
            use_agent: Si True, usa el agente para interpretar directrices
            
        Returns:
            Tupla (poema, directiva) donde directiva contiene la interpretación del agente
        """
        
        if self.model is None:
            # Fallback: generación básica con plantilla
            return self._generate_fallback(prompt), None
        
        try:
            # Usar el agente para interpretar las directrices
            if use_agent:
                structured_prompt, directive = self.agent.generate_prompt(prompt)
                concept = directive.main_concept.lower()
            else:
                # Modo simple: usar el prompt directamente
                structured_prompt = f"Tema: {prompt}\n\nPoema sobre {prompt}:\n\n{prompt.capitalize()} es"
                concept = prompt.strip().lower()
                directive = None
            
            # Intentar usar LM Studio para generación si está disponible y preferido
            if prefer_lm_studio and self.lm_studio_client and self.lm_studio_client.is_available():
                if use_agent and directive:
                    # Convertir directive a dict para LM Studio
                    directive_dict = {
                        "main_concept": directive.main_concept,
                        "style": directive.style,
                        "emotion": directive.emotion,
                        "length": directive.length,
                        "elements": directive.elements,
                        "constraints": directive.constraints
                    }
                    lm_poem = self.lm_studio_client.generate_poem(
                        directive=directive_dict,
                        max_tokens=max_length,
                        temperature=temperature
                    )
                    if lm_poem:
                        print("✓ Poema generado con LM Studio")
                        return lm_poem, directive
                else:
                    # Generación simple con LM Studio
                    lm_poem = self.lm_studio_client.generate(
                        prompt=structured_prompt,
                        max_tokens=max_length,
                        temperature=temperature,
                        system_prompt="Eres un poeta experto. Escribe poemas en español de alta calidad."
                    )
                    if lm_poem:
                        print("✓ Poema generado con LM Studio")
                        return lm_poem, directive
            
            # Si LM Studio no está disponible o no se prefiere, usar modelo local
            prompt_text = structured_prompt
            
            # Tokenizar
            inputs = self.tokenizer.encode(prompt_text, return_tensors="pt")
            inputs = inputs.to(self.device)
            
            # Generar con parámetros mejorados para mayor coherencia y seguimiento del prompt
            # Calcular max_new_tokens (tokens nuevos, sin contar el prompt)
            prompt_length = inputs.shape[1]
            max_new_tokens = max_length - prompt_length if max_length > prompt_length else max_length
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=max_new_tokens,  # Usar max_new_tokens en lugar de max_length
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.85,  # Reducido para seguir más el prompt
                    top_k=35,  # Reducido para seguir más el prompt
                    repetition_penalty=1.3,  # Aumentado de 1.2 para evitar repeticiones
                    no_repeat_ngram_size=3,  # Evitar repetición de trigramas
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,  # Detener en token de fin
                    num_return_sequences=1,
                    early_stopping=True
                )
            
            # Decodificar
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extraer solo el poema generado (sin el prompt)
            # Limpiar el prompt de manera más agresiva
            poem = generated_text
            
            # Lista de variantes del prompt a eliminar (ordenadas de más específicas a menos específicas)
            prompt_variants = [
                prompt_text,  # El prompt exacto usado
                f"Tema: {concept}\n\nPoema sobre {concept}:\n\n{concept.capitalize()} es",
                f"Tema: {concept}\n\nPoema sobre {concept}:\n\n",
                f"Poema sobre {concept}:\n\n",
                f"Escribe un poema sobre {concept}:\n\n",
                f"Poema sobre {prompt}:\n\n",
                f"Escribe un poema sobre {prompt}:\n\n",
            ]
            
            # Eliminar todas las variantes del prompt
            for variant in prompt_variants:
                if variant in poem:
                    poem = poem.replace(variant, "").strip()
            
            # Limpiar caracteres residuales al inicio (comillas, comas, espacios)
            import re
            # Eliminar comillas al inicio
            poem = re.sub(r'^["\'«»]+', '', poem)
            # Eliminar comas seguidas de espacios al inicio
            poem = re.sub(r'^,\s*', '', poem)
            # Eliminar puntos y comas al inicio
            poem = re.sub(r'^[.;]\s*', '', poem)
            # Eliminar espacios múltiples al inicio
            poem = poem.lstrip()
            
            # Limpiar repeticiones del prompt al inicio (patrones como "En X, X,")
            poem_lines = poem.split('\n')
            cleaned_lines = []
            for i, line in enumerate(poem_lines):
                line_lower = line.lower().strip()
                # Detectar líneas que son repeticiones del prompt
                if i < 2:  # Solo verificar las primeras 2 líneas
                    # Patrones comunes de repetición
                    if any(pattern in line_lower for pattern in [
                        f"en {concept.lower()}, {concept.lower()},",
                        f"{concept.lower()}, {concept.lower()},",
                        f"poema sobre {concept.lower()}",
                        f"tema: {concept.lower()}",
                    ]) and len(line.split(',')) > 2:  # Si tiene muchas comas, probablemente es repetición
                        continue  # Saltar esta línea
                cleaned_lines.append(line)
            
            poem = '\n'.join(cleaned_lines).strip()
            
            # Limpiar líneas que empiezan con el prompt repetido
            lines = poem.split('\n')
            final_lines = []
            for line in lines:
                line_stripped = line.strip()
                # Si la línea es muy similar al prompt o concepto, saltarla
                if line_stripped and len(line_stripped) < 100:
                    line_lower = line_stripped.lower()
                    # Detectar si es una variación del prompt
                    if (concept and concept.lower() in line_lower and 
                        any(word in line_lower for word in ['poema', 'tema', 'sobre', 'escribe']) and
                        line_lower.count(concept.lower()) > 1):  # Si el concepto aparece más de una vez
                        continue
                final_lines.append(line)
            
            poem = '\n'.join(final_lines).strip()
            
            # Validar que el concepto aparezca en el poema
            # Si no aparece, hacer múltiples intentos con diferentes estrategias
            max_retries = 3
            retry_count = 0
            concept_words = concept.split() if concept else []
            
            while retry_count < max_retries:
                # Verificar si el concepto o sus palabras clave aparecen
                poem_lower = poem.lower()
                concept_found = False
                
                if concept and len(concept) > 2:
                    # Verificar concepto completo
                    if concept in poem_lower:
                        concept_found = True
                    # Verificar palabras individuales del concepto (si tiene más de una palabra)
                    elif len(concept_words) > 1:
                        # Al menos 2 palabras del concepto deben aparecer
                        words_found = sum(1 for word in concept_words if len(word) > 3 and word in poem_lower)
                        if words_found >= min(2, len(concept_words)):
                            concept_found = True
                    # Si es una sola palabra, debe aparecer
                    elif len(concept_words) == 1 and concept_words[0] in poem_lower:
                        concept_found = True
                
                if concept_found or not concept or len(poem) < 20:
                    break
                
                # Si el concepto no aparece, regenerar con estrategias más agresivas
                retry_count += 1
                print(f"⚠ Concepto '{concept}' no encontrado en el poema. Reintento {retry_count}/{max_retries}...")
                
                # Estrategia: prompt más enfático y temperatura más baja
                if retry_count == 1:
                    # Primera regeneración: prompt más directo
                    prompt_text = f"Tema: {concept}\n\nPoema sobre {concept}:\n\nEn la {concept}, la {concept} es"
                elif retry_count == 2:
                    # Segunda regeneración: aún más directo
                    prompt_text = f"{concept.capitalize()}. Poema sobre {concept}:\n\n{concept.capitalize()}, {concept},"
                else:
                    # Tercera regeneración: forzar inicio con el concepto
                    prompt_text = f"{concept.capitalize()} es el tema. Escribe un poema:\n\n{concept.capitalize()}"
                
                inputs = self.tokenizer.encode(prompt_text, return_tensors="pt")
                inputs = inputs.to(self.device)
                
                # Calcular max_new_tokens para el retry también
                prompt_length_retry = inputs.shape[1]
                max_new_tokens_retry = max_length - prompt_length_retry if max_length > prompt_length_retry else max_length
                
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs,
                        max_new_tokens=max_new_tokens_retry,
                        temperature=max(0.4, temperature - 0.3),  # Reducir temperatura significativamente
                        do_sample=True,
                        top_p=0.75,  # Más restrictivo
                        top_k=25,  # Más restrictivo
                        repetition_penalty=1.3,
                        no_repeat_ngram_size=3,
                        pad_token_id=self.tokenizer.eos_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                        num_return_sequences=1,
                        early_stopping=True
                    )
                
                generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                poem = generated_text
                
                # Limpiar caracteres residuales al inicio
                import re
                poem = re.sub(r'^["\'«»]+', '', poem)
                poem = re.sub(r'^,\s*', '', poem)
                poem = re.sub(r'^[.;]\s*', '', poem)
                poem = poem.lstrip()
                
                # Limpiar el prompt
                for prompt_variant in [
                    prompt_text,
                    f"Tema: {concept}\n\nPoema sobre {concept}:\n\n",
                    f"{concept.capitalize()}. Poema sobre {concept}:\n\n",
                ]:
                    if prompt_variant in poem:
                        poem = poem.replace(prompt_variant, "").strip()
                        break
                
                poem = self._format_poem(poem)
            
            # Si después de todos los intentos el concepto no aparece, intentar una última estrategia
            if concept and concept not in poem.lower() and len(poem) > 20:
                print(f"⚠ Advertencia: El concepto '{concept}' no aparece claramente en el poema generado")
                # En lugar de agregar una línea mal formateada, intentar insertar el concepto de manera natural
                # Solo si el poema tiene al menos algunas líneas
                poem_lines = poem.split('\n')
                if len(poem_lines) >= 2:
                    # Intentar insertar el concepto en la primera línea de manera natural
                    first_line = poem_lines[0]
                    if concept not in first_line.lower():
                        # Crear una línea introductoria más natural
                        concept_variants = [
                            f"El {concept}",
                            f"Un {concept}",
                            f"La {concept}",
                            concept.capitalize()
                        ]
                        # Usar la variante más apropiada según el género del concepto
                        if concept.endswith('a'):
                            intro = f"La {concept}"
                        elif concept.endswith('o'):
                            intro = f"El {concept}"
                        else:
                            intro = concept.capitalize()
                        
                        # Solo agregar si no hace que el poema se vea raro
                        if len(poem) > 50:  # Solo si el poema es suficientemente largo
                            poem_lines.insert(0, f"{intro},")
                            poem = '\n'.join(poem_lines)
            
            # Limpiar y formatear
            # Convertir max_length (tokens) a caracteres aproximados (1 token ≈ 4 caracteres en español)
            max_chars = int(max_length * 4) if max_length else None
            poem = self._format_poem(poem, max_length_chars=max_chars)
            
            return poem, directive
            
        except Exception as e:
            print(f"Error en la generación: {e}")
            return self._generate_fallback(prompt), None
    
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
    
    def _format_poem(self, text: str, max_length_chars: int = None) -> str:
        """
        Formatear el poema generado basado en frases completas
        
        Args:
            text: Texto del poema
            max_length_chars: Longitud máxima aproximada en caracteres (se usa para calcular frases)
        """
        import re
        
        # Dividir en líneas y limpiar
        lines = text.split('\n')
        formatted_lines = []
        
        import re
        
        for line in lines:
            line = line.strip()
            
            # Limpiar caracteres residuales al inicio de cada línea
            # Eliminar comillas al inicio
            line = re.sub(r'^["\'«»]+', '', line)
            # Eliminar comas seguidas de espacios al inicio
            line = re.sub(r'^,\s*', '', line)
            # Eliminar puntos y comas al inicio
            line = re.sub(r'^[.;]\s*', '', line)
            line = line.strip()
            
            # Filtrar líneas vacías o muy cortas
            if line and len(line) > 2:
                # Filtrar líneas que son claramente metadatos o prompts
                line_lower = line.lower()
                if any(word in line_lower for word in ['tema:', 'poema sobre', 'escribe un poema', 'instrucción:']):
                    # Si contiene palabras clave de prompt pero es muy corta, probablemente es metadata
                    if len(line) < 50:
                        continue
                formatted_lines.append(line)
        
        # Si hay muy pocas líneas, intentar dividir por puntos
        if len(formatted_lines) < 3:
            sentences = text.split('.')
            formatted_lines = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        # Limpiar líneas duplicadas o muy similares al inicio
        if len(formatted_lines) > 1:
            # Si las primeras dos líneas son muy similares, eliminar una
            if formatted_lines[0].lower() == formatted_lines[1].lower():
                formatted_lines.pop(0)
        
        # Unir todas las líneas
        full_text = '\n'.join(formatted_lines)
        
        # Si hay límite, usar sistema basado en frases completas
        if max_length_chars:
            # Estimar número de frases objetivo (asumiendo ~50-80 caracteres por frase)
            avg_chars_per_sentence = 65
            target_sentences = max(3, int(max_length_chars / avg_chars_per_sentence))
            
            # Detectar frases completas usando regex
            # Una frase termina en: punto, exclamación, interrogación seguido de espacio o fin de línea
            # También considerar fin de línea como separador de frase
            sentence_pattern = r'([^.!?\n]+[.!?]+(?:\s|$)|[^.!?\n]+\n)'
            sentences = re.findall(sentence_pattern, full_text)
            
            # Si no se detectan suficientes frases con el patrón, dividir por líneas
            if len(sentences) < target_sentences:
                # Dividir por líneas y considerar cada línea como una frase potencial
                line_sentences = []
                for line in formatted_lines:
                    # Si la línea termina en puntuación, es una frase completa
                    if line.rstrip().endswith(('.', '!', '?', ';', ':')):
                        line_sentences.append(line)
                    # Si no, buscar puntuación dentro de la línea
                    else:
                        # Dividir por puntuación dentro de la línea
                        line_parts = re.split(r'([.!?]+)', line)
                        for i in range(0, len(line_parts) - 1, 2):
                            if i + 1 < len(line_parts):
                                phrase = line_parts[i] + line_parts[i+1]
                                if phrase.strip():
                                    line_sentences.append(phrase.strip())
                            elif line_parts[i].strip():
                                line_sentences.append(line_parts[i].strip())
                
                if line_sentences:
                    sentences = line_sentences
            
            # Limpiar frases encontradas
            cleaned_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 5:  # Filtrar frases muy cortas
                    # Filtrar metadatos
                    if not any(word in sentence.lower() for word in ['tema:', 'poema sobre', 'escribe']):
                        cleaned_sentences.append(sentence)
            
            if cleaned_sentences:
                # Tomar solo el número de frases objetivo
                selected_sentences = cleaned_sentences[:target_sentences]
                result = '\n'.join(selected_sentences)
                
                # Verificar que no exceda demasiado el límite (máximo 20% más)
                if len(result) > max_length_chars * 1.2:
                    # Si excede, reducir frases hasta que quepa
                    while len(result) > max_length_chars * 1.2 and len(selected_sentences) > 1:
                        selected_sentences.pop()
                        result = '\n'.join(selected_sentences)
                
                # Asegurar que termine en una frase completa (punto, exclamación, interrogación)
                if result and not result.rstrip().endswith(('.', '!', '?', ';', ':')):
                    # Buscar la última frase completa
                    last_sentence_end = max(
                        result.rfind('.'),
                        result.rfind('!'),
                        result.rfind('?'),
                        result.rfind(';'),
                        result.rfind(':')
                    )
                    if last_sentence_end > len(result) * 0.5:  # Si la última frase completa está al menos a la mitad
                        result = result[:last_sentence_end + 1].strip()
                
                return result
            else:
                # Fallback: si no se detectan frases, usar el método anterior pero mejorado
                if len(full_text) > max_length_chars:
                    # Buscar el último punto de corte natural antes del límite
                    cut_pos = max_length_chars
                    
                    # Buscar hacia atrás el mejor punto de corte
                    for i in range(cut_pos, max(int(cut_pos * 0.6), 0), -1):
                        if full_text[i] in '.!?;:':
                            # Verificar que hay un espacio después o es el final
                            if i == len(full_text) - 1 or full_text[i+1] in ' \n':
                                result = full_text[:i+1].strip()
                                return result
                    
                    # Si no encuentra, buscar fin de línea
                    last_newline = full_text.rfind('\n', 0, cut_pos)
                    if last_newline > cut_pos * 0.7:
                        return full_text[:last_newline].strip()
                    
                    # Último recurso: cortar en espacio
                    last_space = full_text.rfind(' ', 0, cut_pos)
                    if last_space > cut_pos * 0.8:
                        return full_text[:last_space].strip() + '...'
                    
                    return full_text[:cut_pos].strip() + '...'
        
        # Sin límite, devolver todas las líneas (máximo 50 para evitar poemas muy largos)
        return '\n'.join(formatted_lines[:50])

