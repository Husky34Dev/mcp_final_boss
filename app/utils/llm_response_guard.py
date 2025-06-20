"""
Validador de respuestas del LLM para asegurar que no se inventen datos cuando se requieren herramientas.
Permite extender reglas y políticas fácilmente.
"""
from typing import Optional, Dict, Any
from app.config.context_config import context_config

class LLMResponseGuard:
    """
    Clase abstracta y extensible para validar respuestas del LLM.
    Se asegura de que, si la consulta requiere datos reales, la respuesta provenga de una herramienta.
    """
    def validate(self, user_message: str, llm_response: str, tool_call_executed: bool) -> Optional[str]:
        """
        Valida la respuesta del LLM.
        Args:
            user_message: Mensaje original del usuario.
            llm_response: Respuesta generada por el LLM (texto plano).
            tool_call_executed: Si se ejecutó alguna herramienta.
        Returns:
            None si la respuesta es válida, o un string con el motivo del rechazo si no lo es.
        """
        if context_config.requires_real_data(user_message) and not tool_call_executed:
            return (
                "La consulta requiere datos reales, pero no se ha consultado la API. "
                "Por favor, asegúrate de proporcionar un identificador válido (por ejemplo, DNI) "
                "o reformula tu pregunta para que el sistema pueda consultar la base de datos."
            )
        return None

    # Método para extender con más reglas en el futuro
    def add_custom_rule(self, rule_func):
        """
        Permite añadir reglas personalizadas de validación.
        rule_func debe aceptar los mismos argumentos que validate y devolver None o un string de error.
        """
        old_validate = self.validate
        def new_validate(user_message, llm_response, tool_call_executed):
            result = old_validate(user_message, llm_response, tool_call_executed)
            if result is not None:
                return result
            return rule_func(user_message, llm_response, tool_call_executed)
        self.validate = new_validate
