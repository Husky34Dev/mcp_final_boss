"""
ConversationContext: Manejo abstracto y extensible del contexto conversacional.
Permite almacenar y actualizar información relevante de la conversación (DNI, nombre, tipo de consulta, etc).
"""
from typing import Dict, Any, Optional
from app.utils.context_validator import ContextValidator

class ConversationContext:
    def __init__(self, extractors=None):
        self.data: Dict[str, Any] = {}
        self.validator = ContextValidator()
        # Lista de extractores de contexto (puedes añadir más en el futuro)
        self.extractors = extractors or [self.extract_dni, self.extract_query_type]

    def update(self, user_message: str) -> None:
        """
        Actualiza el contexto a partir del mensaje del usuario.
        Extrae y guarda DNI y tipo de consulta si están presentes.
        """
        self.data['last_message'] = user_message
        self.data['requires_real_data'] = self.validator.requires_real_data(user_message)
        self.data['is_referential'] = self.validator.is_referential_query(user_message)
        for extractor in self.extractors:
            extractor(user_message)

    def extract_dni(self, message: str) -> None:
        import re
        match = re.search(r"\b\d{8}[A-Za-z]\b", message)
        if match:
            self.data['dni'] = match.group(0).upper()

    def extract_query_type(self, message: str) -> None:
        """
        Devuelve el tipo de consulta detectado (por ejemplo, 'factura', 'incidencia', 'abonado') o None.
        """
        message_lower = message.lower()
        for tipo, keywords in self.validator.config.query_types.items():
            if any(kw in message_lower for kw in keywords):
                self.data['query_type'] = tipo
                return
        if "abonado" in message_lower:
            self.data['query_type'] = "abonado"

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def clear(self) -> None:
        self.data.clear()

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.data)

    def get_referential_prompt(self) -> str:
        """
        Devuelve un bloque de contexto elegante para inyectar en el prompt si la consulta es referencial.
        """
        if self.get('dni'):
            return f"Reference context: The previous DNI used in this conversation is {self.get('dni')}."
        return ""
