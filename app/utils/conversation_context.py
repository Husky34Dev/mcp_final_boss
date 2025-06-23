"""
ConversationContext: Manejo del estado de la conversación.
Mantiene y actualiza el contexto usando el ContextManager centralizado.
"""
from typing import Dict, Any, Optional
from app.config.context_config import context_config
import logging

class ConversationContext:
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self._referential_fields = {'query_type', 'dni', 'ubicacion'}  # campos que se heredan en consultas referenciales

    def update(self, user_message: str) -> None:
        """
        Actualiza el contexto a partir del mensaje del usuario.
        En consultas referenciales, mantiene el contexto anterior para campos clave.
        """
        # Store previous state for referential handling
        prev_data = dict(self.data)
        
        # Almacena el mensaje y flags de validación básica
        self.data['last_message'] = user_message
        self.data['requires_real_data'] = context_config.requires_real_data(user_message)
        self.data['is_referential'] = context_config.is_referential_query(user_message)
        # Si no se detecta referencia explícita pero la consulta mantiene el mismo tipo, tratamos como referencial
        new_query_type = context_config.detect_query_type(user_message)
        if not self.data['is_referential'] and 'query_type' in prev_data and prev_data['query_type'] == new_query_type:
            self.data['is_referential'] = True

        # Extract query type first (ya obtenido arriba)
        # Handle query type inheritance for referential queries
        if self.data['is_referential']:
            if new_query_type == 'unknown' and 'query_type' in prev_data:
                # If referential and no new query type, keep previous
                self.data['query_type'] = prev_data['query_type']
            elif new_query_type:
                # If referential but has new query type, use new one
                self.data['query_type'] = new_query_type
            else:
                # If truly unknown, use unknown
                self.data['query_type'] = 'unknown'
        else:
            # Not referential, just use new query type
            self.data['query_type'] = new_query_type
        
        # Extract all fields defined in the configuration
        required_fields = context_config.get_required_fields(self.data['query_type'])
        for field_name in context_config.fields:
            new_value = context_config.extract_field(field_name, user_message)
            if new_value and new_value.strip():  # Verificar que no sea una cadena vacía
                # Only set field if it's required for this query type or inherited in referential queries
                if field_name in required_fields or (self.data['is_referential'] and field_name in self._referential_fields):
                    self.data[field_name] = new_value
            elif self.data.get('is_referential') and field_name in prev_data and field_name in self._referential_fields:
                # In referential queries, keep previous value for designated fields
                self.data[field_name] = prev_data[field_name]
            else:
                # Clear fields that aren't required for the current query type
                if field_name not in required_fields:
                    self.data.pop(field_name, None)
        
        # Log the initial state of the context
        logging.debug(f"Initial context before applying field rules: {self.data}")

        def should_remove_field(field: str, rules: Dict[str, Any], context: Dict[str, Any], prev_context: Dict[str, Any]) -> bool:
            """
            Determina si un campo debe ser eliminado según las reglas y el estado del contexto.
            """
            if field == 'dni':
                # Condicionar eliminación de 'dni'
                return bool(context.get('is_referential') and field in prev_context and field not in context.get('last_message', ''))
            return field in rules.get('remove', [])

        # Aplicar reglas de herencia y eliminación según el tipo de consulta
        field_rules = context_config.get_field_rules(self.data['query_type'])
        if field_rules:
            # Eliminar campos según las reglas
            for field in field_rules.get('remove', []):
                if should_remove_field(field, field_rules, self.data, prev_data):
                    self.data.pop(field, None)
            # Heredar campos según las reglas
            for field in field_rules.get('inherit', []):
                if field in prev_data:
                    self.data[field] = prev_data[field]

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
        Devuelve un bloque de contexto estructurado para inyectar en el prompt si la consulta es referencial.
        """
        context_items = []
        for key, value in self.data.items():
            if key in self._referential_fields and value:
                context_items.append(f"- **{key.capitalize()}:** {value}")
        if context_items:
            return "### Contexto Referencial\n" + "\n".join(context_items)
        return ""

    def validate_context(self) -> Optional[Dict[str, str]]:
        """
        Valida el contexto actual usando el ContextManager.
        Returns:
            None si el contexto es válido, o un diccionario con los campos faltantes y sus mensajes de error.
        """
        missing_fields = context_config.validate_context(self.data)
        if missing_fields:
            error_messages = {}
            for field in missing_fields:
                if field == 'dni':
                    error_messages[field] = (
                        "Perdona, ha habido un fallo: no pude identificar tu DNI. "
                        "Por favor, reformula tu consulta incluyendo el DNI u otro dato clave."
                    )
                elif field == 'tipo_consulta':
                    error_messages[field] = (
                        "No entendí el tipo de consulta. "
                        "Por favor, indique si desea consultar facturas, datos del abonado, incidencias u otra información."
                    )
                else:
                    error_messages[field] = f"{field}. Por favor, proporcione esta información."
            return error_messages
        return None
