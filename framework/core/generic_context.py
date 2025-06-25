from typing import Any, Dict, Optional
from .context_manager import FrameworkContextManager
import logging

class GenericConversationContext:
    """
    Gestor genérico de contexto conversacional basado en un FrameworkContextManager.
    Maneja actualización de contexto, extracción de campos y aplicación de reglas.
    """
    def __init__(self, context_manager: FrameworkContextManager):
        self.cm = context_manager
        self.data: Dict[str, Any] = {}

    def update(self, user_message: str) -> None:
        prev = dict(self.data)
        self.data['last_message'] = user_message
        self.data['requires_real_data'] = self.cm.requires_real_data(user_message)
        self.data['is_referential'] = self.cm.is_referential(user_message)
        qtype = self.cm.detect_query_type(user_message)
        
        # ❌ REMOVIDO: Lógica incorrecta que forzaba referencialidad
        # La detección de referencialidad debe ser SOLO por contenido del mensaje
        # not por query_type repetido
            
        self.data['query_type'] = qtype
        
        # Extraer valores de campos
        for field in self.cm.fields:
            val = self.cm.extract_field(field, user_message)
            if val:
                self.data[field] = val
                
        # Aplicar reglas de eliminación e herencia
        rules = self.cm.get_field_rules(qtype) or {}
        
        # eliminación
        for field in rules.get('remove', []):
            if field in self.data:
                logging.debug(f"Removing field {field}")
                self.data.pop(field, None)
                
        # herencia
        for field in rules.get('inherit', []):
            if field in prev:
                logging.debug(f"Inheriting field {field}")
                self.data[field] = prev[field]

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.data)

    def get_referential_prompt(self) -> str:
        """
        Construye un bloque de contexto referencial según reglas de herencia.
        """
        qtype = self.data.get('query_type', '')
        rules = self.cm.get_field_rules(qtype) or {}
        items = []
        for field in rules.get('inherit', []):
            if field in self.data and self.data[field] is not None:
                items.append(f"- **{field.capitalize()}:** {self.data[field]}")
        if items:
            return "### Contexto Referencial\n" + "\n".join(items)
        return ""

    def validate_context(self) -> Optional[Dict[str, str]]:
        """
        Valida el contexto según las reglas configuradas.
        Ahora preserva los mensajes personalizados del ContextManager.
        """
        missing_messages = self.cm.validate_context(self.data)
        if missing_messages:
            # Crear dict con índices para compatibilidad con agent.py
            # pero preservando los mensajes personalizados
            result = {}
            for i, message in enumerate(missing_messages):
                result[f"error_{i}"] = message
            return result
        return None
