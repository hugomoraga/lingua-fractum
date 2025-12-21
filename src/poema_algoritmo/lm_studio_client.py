"""
Cliente para integrar LM Studio con el sistema de poesía
LM Studio expone una API compatible con OpenAI en localhost
"""
import os
import requests
from typing import Optional, Dict, Any
import json


class LMStudioClient:
    """
    Cliente para comunicarse con LM Studio
    LM Studio debe estar corriendo con un modelo cargado
    """
    
    def __init__(self, base_url: str = "http://localhost:1234/v1", timeout: int = 60):
        """
        Inicializa el cliente de LM Studio
        
        Args:
            base_url: URL base de la API de LM Studio (default: http://localhost:1234/v1)
            timeout: Timeout para las peticiones en segundos
        """
        self.base_url = base_url
        self.timeout = timeout
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Verifica si LM Studio está disponible"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=2
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def is_available(self) -> bool:
        """Verifica si LM Studio está disponible"""
        return self.available
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Genera texto usando LM Studio
        
        Args:
            prompt: Prompt para la generación
            max_tokens: Máximo número de tokens a generar
            temperature: Temperatura para la generación
            system_prompt: Prompt del sistema (opcional)
            
        Returns:
            Texto generado o None si hay error
        """
        if not self.available:
            return None
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": "local-model",  # LM Studio usa "local-model" como nombre
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"Error en LM Studio: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con LM Studio: {e}")
            self.available = False
            return None
    
    def interpret_directive(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Usa LM Studio para interpretar las directrices del usuario de manera más inteligente
        
        Args:
            user_input: Input del usuario en lenguaje natural
            
        Returns:
            Diccionario con la interpretación estructurada o None si hay error
        """
        if not self.available:
            return None
        
        system_prompt = """Eres un asistente experto en interpretar directrices para generar poesía.
Analiza el input del usuario y extrae la siguiente información en formato JSON:
{
    "main_concept": "el concepto principal del poema",
    "style": "estilo (soneto, haiku, verso libre, romántico, moderno, clásico, etc.) o null",
    "emotion": "emoción/tono (triste, alegre, nostálgico, amoroso, oscuro, sereno, etc.) o null",
    "length": "longitud (corto, medio, largo) o null",
    "elements": ["lista de elementos mencionados como naturaleza, colores, etc."],
    "constraints": ["restricciones o requisitos específicos"]
}

Responde SOLO con el JSON, sin texto adicional."""

        user_prompt = f"Analiza esta directriz para generar poesía: {user_input}"
        
        response = self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=300,
            temperature=0.3  # Baja temperatura para respuestas más deterministas
        )
        
        if not response:
            return None
        
        try:
            # Limpiar la respuesta (puede tener markdown code blocks)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"Error al parsear respuesta de LM Studio: {e}")
            print(f"Respuesta recibida: {response}")
            return None
    
    def generate_poem(
        self,
        directive: Dict[str, Any],
        max_tokens: int = 300,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Genera un poema usando LM Studio basado en directrices estructuradas
        
        Args:
            directive: Diccionario con las directrices interpretadas
            max_tokens: Máximo número de tokens
            temperature: Temperatura para la generación
            
        Returns:
            Poema generado o None si hay error
        """
        if not self.available:
            return None
        
        # Construir prompt estructurado
        parts = []
        if directive.get("main_concept"):
            parts.append(f"Tema: {directive['main_concept']}")
        if directive.get("style"):
            parts.append(f"Estilo: {directive['style']}")
        if directive.get("emotion"):
            parts.append(f"Tono: {directive['emotion']}")
        if directive.get("length"):
            parts.append(f"Longitud: {directive['length']}")
        if directive.get("elements"):
            parts.append(f"Elementos: {', '.join(directive['elements'])}")
        
        structured_prompt = "\n".join(parts) if parts else f"Tema: {directive.get('main_concept', 'poesía')}"
        
        system_prompt = """Eres un poeta experto. Escribe poemas en español de alta calidad.
Sigue las directrices proporcionadas y crea poemas con coherencia, ritmo y belleza poética.
Responde SOLO con el poema, sin explicaciones adicionales."""
        
        user_prompt = f"{structured_prompt}\n\nEscribe el poema:\n\n"
        
        return self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

