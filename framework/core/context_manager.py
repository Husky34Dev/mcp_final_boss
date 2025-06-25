"""
Contexto conversacional simple y unificado.
Reemplaza la complejidad de ContextManager + GenericContext.
"""
import re
import json
import logging
from typing import Any, Dict, Optional, List


class SimpleConversationContext:
    """
    Contexto conversacional simple que maneja todo en una sola clase.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.data: Dict[str, Any] = {}
        self.config = {}
        
        # Cargar configuración si se proporciona
        if config_path:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                logging.warning(f"No se pudo cargar configuración desde {config_path}: {e}")
                self.config = {}
        
        # Configuración por defecto
        self._setup_defaults()
    
    def _setup_defaults(self):
        """Configuración por defecto minimalista si no hay archivo."""
        if not self.config:
            self.config = {
                "real_data_required": [],
                "no_data_indicators": ["ejemplo", "prueba", "test", "demo", "simulación"],
                "reference_indicators": ["este", "estos", "sus", "su", "mismo", "anterior", "ese", "esa"],
                "query_types": {},
                "field_definitions": {},
                "field_rules": {},
                "error_messages": {}
            }
    
    def update(self, user_message: str) -> None:
        """Actualiza el contexto con un nuevo mensaje."""
        prev_data = dict(self.data)
        
        self.data['last_message'] = user_message
        self.data['query_type'] = self._detect_query_type(user_message)
        self.data['is_referential'] = self._is_referential(user_message)
        self.data['requires_real_data'] = self._requires_real_data(user_message)
        
        # Extraer campos del mensaje
        self._extract_fields(user_message)
        
        # Aplicar reglas de herencia
        self._apply_inheritance_rules(prev_data)
    
    def _detect_query_type(self, text: str) -> str:
        """Detecta el tipo de consulta basado en palabras clave."""
        text_lower = text.lower()
        query_types = self.config.get("query_types", {})
        
        for qtype, keywords in query_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return qtype
        
        return "generic"
    
    def _is_referential(self, text: str) -> bool:
        """Detecta si el mensaje hace referencia a contexto anterior."""
        text_lower = text.lower()
        indicators = self.config.get("reference_indicators", [])
        return any(indicator in text_lower for indicator in indicators)
    
    def _requires_real_data(self, text: str) -> bool:
        """Determina si la consulta requiere datos reales."""
        text_lower = text.lower()
        
        # Si tiene indicadores de NO datos reales
        no_data_indicators = self.config.get("no_data_indicators", [])
        if any(indicator in text_lower for indicator in no_data_indicators):
            return False
        
        # Si el tipo de consulta requiere datos reales
        query_type = self._detect_query_type(text)
        real_data_required = self.config.get("real_data_required", [])
        return query_type in real_data_required
    
    def _extract_fields(self, text: str) -> None:
        """Extrae campos del texto usando patrones regex."""
        field_definitions = self.config.get("field_definitions", {})
        
        for field_name, field_config in field_definitions.items():
            patterns = field_config.get("patterns", [])
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Tomar la primera coincidencia
                    value = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    self.data[field_name] = value
                    break
    
    def _apply_inheritance_rules(self, prev_data: Dict[str, Any]) -> None:
        """Aplica reglas de herencia desde el contexto anterior."""
        query_type = self.data.get('query_type', '')
        field_rules = self.config.get("field_rules", {})
        rules = field_rules.get(query_type, {})
        
        # Herencia de campos
        for field in rules.get('inherit', []):
            if field in prev_data and field not in self.data:
                self.data[field] = prev_data[field]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor del contexto."""
        return self.data.get(key, default)
    
    def as_dict(self) -> Dict[str, Any]:
        """Retorna el contexto como diccionario."""
        return dict(self.data)
    
    def get_referential_prompt(self) -> str:
        """Construye prompt de contexto referencial."""
        if not self.data.get('is_referential'):
            return ""
        
        query_type = self.data.get('query_type', '')
        field_rules = self.config.get("field_rules", {})
        rules = field_rules.get(query_type, {})
        
        items = []
        for field in rules.get('inherit', []):
            if field in self.data and self.data[field] is not None:
                items.append(f"- **{field.capitalize()}:** {self.data[field]}")
        
        if items:
            return "### Contexto Referencial\n" + "\n".join(items)
        return ""
    
    def validate_context(self) -> Optional[Dict[str, str]]:
        """Valida que el contexto tenga los campos requeridos."""
        query_type = self.data.get('query_type', '')
        field_rules = self.config.get("field_rules", {})
        rules = field_rules.get(query_type, {})
        error_messages = self.config.get("error_messages", {})
        
        missing_fields = {}
        
        for field in rules.get('require', []):
            if field not in self.data or not self.data[field]:
                error_msg = error_messages.get(field, f"Falta el campo requerido: {field}")
                missing_fields[field] = error_msg
        
        return missing_fields if missing_fields else None
