"""
Agente inteligente para interpretar directrices y generar poesía
"""
import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PoetryDirective:
    """Estructura para almacenar directrices interpretadas"""
    main_concept: str
    style: Optional[str] = None
    emotion: Optional[str] = None
    length: Optional[str] = None  # corto, medio, largo
    tone: Optional[str] = None  # triste, alegre, melancólico, etc.
    elements: List[str] = None  # elementos adicionales mencionados
    constraints: List[str] = None  # restricciones o requisitos
    
    def __post_init__(self):
        if self.elements is None:
            self.elements = []
        if self.constraints is None:
            self.constraints = []


class PoetryAgent:
    """
    Agente que interpreta directrices en lenguaje natural y genera prompts estructurados
    para la generación de poesía.
    Puede usar LM Studio para interpretación más inteligente si está disponible.
    """
    
    def __init__(self, use_lm_studio: bool = True):
        """
        Inicializa el agente
        
        Args:
            use_lm_studio: Si True, intenta usar LM Studio para interpretación mejorada
        """
        self.use_lm_studio = use_lm_studio
        self.lm_studio_client = None
        
        if use_lm_studio:
            try:
                from .lm_studio_client import LMStudioClient
                lm_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
                self.lm_studio_client = LMStudioClient(base_url=lm_url)
                if self.lm_studio_client.is_available():
                    print("✓ LM Studio detectado y disponible")
                else:
                    print("⚠ LM Studio no disponible, usando interpretación basada en reglas")
                    self.lm_studio_client = None
            except Exception as e:
                print(f"⚠ No se pudo inicializar LM Studio: {e}")
                self.lm_studio_client = None
        # Patrones para detectar conceptos principales
        self.concept_patterns = [
            r'(?:sobre|acerca de|de|del|la|el|un|una)\s+([a-záéíóúñü]+(?:\s+[a-záéíóúñü]+)*)',
            r'^(?:escribe|haz|crea|genera)\s+(?:un\s+)?(?:poema\s+)?(?:sobre\s+)?([a-záéíóúñü]+(?:\s+[a-záéíóúñü]+)*)',
            r'^([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+(?:\s+[a-záéíóúñü]+)*)',  # Palabra capitalizada al inicio
        ]
        
        # Palabras clave para estilos
        self.style_keywords = {
            'soneto': ['soneto'],
            'haiku': ['haiku', 'haikú'],
            'verso libre': ['verso libre', 'libre', 'sin rima'],
            'rima': ['rima', 'rimado', 'con rima'],
            'prosa poética': ['prosa', 'prosa poética'],
            'romántico': ['romántico', 'romántica', 'romance'],
            'moderno': ['moderno', 'moderna', 'contemporáneo'],
            'clásico': ['clásico', 'clásica', 'tradicional'],
        }
        
        # Palabras clave para emociones/tonos
        self.emotion_keywords = {
            'triste': ['triste', 'tristeza', 'melancolía', 'melancólico', 'dolor', 'doloroso'],
            'alegre': ['alegre', 'alegría', 'feliz', 'felicidad', 'gozo', 'gozoso'],
            'nostálgico': ['nostálgico', 'nostalgia', 'recuerdo', 'pasado'],
            'amoroso': ['amor', 'amoroso', 'amorosa', 'cariño', 'pasión', 'pasional'],
            'esperanzado': ['esperanza', 'esperanzado', 'optimista'],
            'oscuro': ['oscuro', 'oscura', 'tenebroso', 'sombrío'],
            'sereno': ['sereno', 'serena', 'tranquilo', 'paz', 'pacífico'],
        }
        
        # Palabras clave para longitud
        self.length_keywords = {
            'corto': ['corto', 'breve', 'pequeño', 'poco'],
            'medio': ['medio', 'moderado', 'normal'],
            'largo': ['largo', 'extenso', 'mucho', 'completo'],
        }
        
        # Palabras de conexión y elementos adicionales
        self.connector_words = ['y', 'con', 'incluyendo', 'que tenga', 'que incluya', 'además']
        self.element_keywords = ['colores', 'animales', 'naturaleza', 'ciudad', 'mar', 'montaña', 
                                 'noche', 'día', 'sol', 'luna', 'estrellas', 'viento', 'lluvia']
    
    def parse_directive(self, user_input: str) -> PoetryDirective:
        """
        Interpreta las directrices del usuario en lenguaje natural
        
        Args:
            user_input: Texto con las directrices del usuario
            
        Returns:
            PoetryDirective con la información interpretada
        """
        # Intentar usar LM Studio primero si está disponible
        if self.lm_studio_client and self.lm_studio_client.is_available():
            lm_interpretation = self.lm_studio_client.interpret_directive(user_input)
            if lm_interpretation:
                # Convertir la interpretación de LM Studio a PoetryDirective
                directive = PoetryDirective(
                    main_concept=lm_interpretation.get("main_concept", ""),
                    style=lm_interpretation.get("style"),
                    emotion=lm_interpretation.get("emotion"),
                    length=lm_interpretation.get("length"),
                    elements=lm_interpretation.get("elements", []),
                    constraints=lm_interpretation.get("constraints", [])
                )
                if directive.main_concept:
                    return directive
                # Si LM Studio no pudo extraer el concepto, continuar con método basado en reglas
        
        # Método basado en reglas (fallback o si LM Studio no está disponible)
        input_lower = user_input.lower().strip()
        directive = PoetryDirective(main_concept="")
        
        # 1. Extraer concepto principal
        directive.main_concept = self._extract_main_concept(user_input, input_lower)
        
        # 2. Detectar estilo
        directive.style = self._detect_keyword(input_lower, self.style_keywords)
        
        # 3. Detectar emoción/tono
        directive.emotion = self._detect_keyword(input_lower, self.emotion_keywords)
        
        # 4. Detectar longitud
        directive.length = self._detect_keyword(input_lower, self.length_keywords)
        
        # 5. Extraer elementos adicionales
        directive.elements = self._extract_elements(input_lower)
        
        # 6. Extraer restricciones
        directive.constraints = self._extract_constraints(input_lower)
        
        return directive
    
    def _extract_main_concept(self, original: str, lower: str) -> str:
        """Extrae el concepto principal del input"""
        # Si es una sola palabra o frase corta, probablemente es el concepto
        words = lower.split()
        if len(words) <= 3:
            return original.strip()
        
        # Buscar patrones comunes - mejorados para encontrar el objeto real
        # Patrón 1: "sobre X" o "acerca de X"
        sobre_pattern = r'(?:sobre|acerca de)\s+(?:un\s+|una\s+|el\s+|la\s+)?([a-záéíóúñü]+(?:\s+[a-záéíóúñü]+){0,2})'
        match = re.search(sobre_pattern, lower)
        if match:
            concept = match.group(1).strip()
            # Filtrar palabras comunes
            stop_words = {'poema', 'poesía', 'escribe', 'haz', 'crea', 'genera', 'sobre', 'acerca', 'del', 'de', 'la', 'el', 'un', 'una', 'los', 'las'}
            concept_words = concept.split()
            # Filtrar stop words del concepto
            filtered_words = [w for w in concept_words if w.lower() not in stop_words]
            if filtered_words:
                return ' '.join(filtered_words)
        
        # Patrón 2: Después de "escribe un poema X sobre Y"
        pattern2 = r'(?:escribe|haz|crea|genera)\s+(?:un\s+)?(?:poema\s+)?(?:[a-záéíóúñü]+\s+)?(?:sobre|acerca de)\s+(?:un\s+|una\s+|el\s+|la\s+)?([a-záéíóúñü]+(?:\s+[a-záéíóúñü]+){0,2})'
        match = re.search(pattern2, lower)
        if match:
            concept = match.group(1).strip()
            stop_words = {'poema', 'poesía', 'escribe', 'haz', 'crea', 'genera', 'sobre', 'acerca', 'del', 'de', 'la', 'el', 'un', 'una'}
            concept_words = concept.split()
            filtered_words = [w for w in concept_words if w.lower() not in stop_words]
            if filtered_words:
                return ' '.join(filtered_words)
        
        # Patrón 3: Buscar después de palabras clave de emoción/estilo
        # Ejemplo: "poema triste sobre gato" -> "gato"
        pattern3 = r'(?:poema|soneto|haiku|verso)\s+(?:[a-záéíóúñü]+\s+)?(?:sobre|acerca de)\s+(?:un\s+|una\s+|el\s+|la\s+)?([a-záéíóúñü]+(?:\s+[a-záéíóúñü]+){0,2})'
        match = re.search(pattern3, lower)
        if match:
            concept = match.group(1).strip()
            stop_words = {'poema', 'poesía', 'sobre', 'acerca', 'del', 'de', 'la', 'el', 'un', 'una'}
            concept_words = concept.split()
            filtered_words = [w for w in concept_words if w.lower() not in stop_words]
            if filtered_words:
                return ' '.join(filtered_words)
        
        # Buscar patrones comunes originales como fallback
        for pattern in self.concept_patterns:
            matches = re.findall(pattern, lower, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    match = match.strip()
                    stop_words = {'sobre', 'acerca', 'del', 'la', 'el', 'un', 'una', 'poema', 'poesía'}
                    if match and match.lower() not in stop_words:
                        return match
        
        # Si no encontramos nada específico, tomar las últimas palabras (probablemente el objeto)
        # En "escribe un poema X sobre Y", Y es lo que queremos
        if len(words) > 3:
            # Tomar las últimas 1-2 palabras como concepto
            last_words = ' '.join(words[-2:])
            return last_words
        
        # Fallback: primeras palabras
        first_words = ' '.join(words[:3])
        return first_words
    
    def _detect_keyword(self, text: str, keyword_dict: Dict[str, List[str]]) -> Optional[str]:
        """Detecta si alguna palabra clave está presente en el texto"""
        for key, keywords in keyword_dict.items():
            for keyword in keywords:
                if keyword in text:
                    return key
        return None
    
    def _extract_elements(self, text: str) -> List[str]:
        """Extrae elementos adicionales mencionados"""
        elements = []
        for keyword in self.element_keywords:
            if keyword in text:
                elements.append(keyword)
        return elements
    
    def _extract_constraints(self, text: str) -> List[str]:
        """Extrae restricciones o requisitos específicos"""
        constraints = []
        
        # Buscar frases que indiquen restricciones
        constraint_patterns = [
            r'(?:no\s+)?(?:debe|debe\s+ser|tiene\s+que|necesita)\s+([^,\.]+)',
            r'(?:sin|sin\s+que)\s+([^,\.]+)',
            r'(?:evitar|evita)\s+([^,\.]+)',
        ]
        
        for pattern in constraint_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            constraints.extend(matches)
        
        return constraints
    
    def build_structured_prompt(self, directive: PoetryDirective) -> str:
        """
        Construye un prompt estructurado basado en las directrices interpretadas
        
        Args:
            directive: PoetryDirective con las directrices
            
        Returns:
            Prompt estructurado para el modelo
        """
        parts = []
        
        # Tema principal (siempre presente)
        if directive.main_concept:
            parts.append(f"Tema: {directive.main_concept}")
        
        # Estilo
        if directive.style:
            parts.append(f"Estilo: {directive.style}")
        
        # Emoción/tono
        if directive.emotion:
            parts.append(f"Tono: {directive.emotion}")
        
        # Longitud
        if directive.length:
            parts.append(f"Longitud: {directive.length}")
        
        # Elementos adicionales
        if directive.elements:
            parts.append(f"Elementos: {', '.join(directive.elements)}")
        
        # Construir el prompt final
        if len(parts) > 1:
            # Si hay múltiples directrices, crear un prompt estructurado
            structured = "\n".join(parts)
            prompt = f"{structured}\n\nPoema:\n\n"
        else:
            # Si solo hay tema, usar formato simple pero enfático
            concept = directive.main_concept
            prompt = f"Tema: {concept}\n\nPoema sobre {concept}:\n\n{concept.capitalize()} es"
        
        return prompt
    
    def generate_prompt(self, user_input: str) -> Tuple[str, PoetryDirective]:
        """
        Proceso completo: interpreta directrices y genera prompt estructurado
        
        Args:
            user_input: Input del usuario en lenguaje natural
            
        Returns:
            Tupla con (prompt_estructurado, directiva_interpretada)
        """
        directive = self.parse_directive(user_input)
        prompt = self.build_structured_prompt(directive)
        return prompt, directive
    
    def get_directive_summary(self, directive: PoetryDirective) -> str:
        """
        Genera un resumen legible de las directrices interpretadas
        Útil para mostrar al usuario qué entendió el agente
        """
        summary_parts = [f"**Tema principal:** {directive.main_concept}"]
        
        if directive.style:
            summary_parts.append(f"**Estilo:** {directive.style}")
        
        if directive.emotion:
            summary_parts.append(f"**Tono:** {directive.emotion}")
        
        if directive.length:
            summary_parts.append(f"**Longitud:** {directive.length}")
        
        if directive.elements:
            summary_parts.append(f"**Elementos:** {', '.join(directive.elements)}")
        
        if directive.constraints:
            summary_parts.append(f"**Restricciones:** {', '.join(directive.constraints)}")
        
        return "\n".join(summary_parts)

