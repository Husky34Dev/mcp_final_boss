"""
ConversationContext: Manejo del estado de la conversación.
Mantiene y actualiza el contexto usando el ContextManager centralizado.
"""
from app.framework.conversation_context import GenericConversationContext
from app.config.context_config import context_config
from typing import Optional, Dict

class ConversationContext(GenericConversationContext):
    """
    Adaptación de GenericConversationContext para la aplicación.
    """
    def __init__(self):
        super().__init__(context_config)

    def validate_context(self) -> Optional[Dict[str, str]]:
        """
        Valida el contexto actual usando el FrameworkContextManager.
        Retorna None si es válido, o un diccionario de errores.
        """
        missing_fields = self.cm.validate_context(self.data)
        if missing_fields:
            error_messages: Dict[str, str] = {}
            for field in missing_fields:
                if 'dni' in field:
                    error_messages['dni'] = (
                        "Perdona, ha habido un fallo: no pude identificar tu DNI. "
                        "Por favor, reformula tu consulta incluyendo el DNI u otro dato clave."
                    )
                elif 'tipo_consulta' in field:
                    error_messages['tipo_consulta'] = (
                        "No entendí el tipo de consulta. "
                        "Por favor, indica si deseas consultar facturas, datos del abonado, incidencias u otra información."
                    )
                else:
                    error_messages[field] = f"{field}. Por favor, proporcione esta información."
            return error_messages
        return None
