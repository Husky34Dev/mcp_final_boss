"""
Guardián de respuestas LLM.
"""
from typing import Optional


class ResponseGuard:
    """
    Guardián que valida las respuestas del LLM para asegurar calidad.
    """
    
    def __init__(self):
        self.min_length = 5
        self.forbidden_phrases = [
            "no puedo",
            "lo siento, no tengo",
            "no tengo acceso",
            "como ia no"
        ]
    
    def validate(self, user_message: str, response: str, tool_executed: bool = False) -> Optional[str]:
        """
        Valida una respuesta del LLM.
        
        Args:
            user_message: Mensaje original del usuario
            response: Respuesta del LLM
            tool_executed: Si se ejecutó alguna herramienta
            
        Returns:
            str: Mensaje de error si la respuesta es inválida, None si es válida
        """
        # Validar que la respuesta no esté vacía
        if not response or not response.strip():
            return "Lo siento, no pude generar una respuesta válida. Por favor, inténtalo de nuevo."
        
        # Validar longitud mínima
        if len(response.strip()) < self.min_length:
            return "La respuesta parece incompleta. Por favor, reformula tu pregunta."
        
        # Validar frases prohibidas (respuestas genéricas sin valor)
        response_lower = response.lower()
        for phrase in self.forbidden_phrases:
            if phrase in response_lower:
                return "No pude procesar tu consulta correctamente. Por favor, proporciona más detalles."
        
        # Si se ejecutó una herramienta pero la respuesta parece genérica
        if tool_executed and any(word in response_lower for word in ["general", "ejemplo", "típico"]):
            return "Obtuve información específica pero la respuesta parece genérica. Por favor, verifica tu consulta."
        
        return None
