"""
Sistema de contexto configurable por JSON.
"""
import json
import re
from typing import Dict, Any, Optional, List


class SimpleContext:
    """Contexto simple para casos básicos."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
    
    def update(self, message: str) -> None:
        """Actualiza el contexto básico."""
        # Extraer DNI si está presente
        dni_match = re.search(r'\\b(\\d{8}[A-Za-z])\\b', message)
        if dni_match:
            self.data['dni'] = dni_match.group(1)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
    
    def as_dict(self) -> Dict[str, Any]:
        return self.data.copy()
    
    def validate_context(self) -> Optional[Dict[str, str]]:
        """Valida el contexto. Retorna dict con errores o None."""
        return None
    
    def get_referential_prompt(self) -> Optional[str]:
        """Obtiene prompt referencial si está disponible."""
        return None


class ConfigurableContext:
    """
    Contexto completamente configurable por JSON.
    """
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.patterns = self._compile_patterns()
        self.data: Dict[str, Any] = {
            'conversation_history': [],
            'last_message': '',
            'fields': {},
            'is_referential': False
        }
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carga configuración desde JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Configuración por defecto si no existe el archivo
            return {
                "query_types": {
                    "generic": ["hola", "adios"],
                    "abonado": ["datos", "abonado"],
                    "factura": ["factura", "pago"], 
                    "incidencia": ["incidencia", "problema"]
                },
                "field_definitions": {
                    "dni": {
                        "patterns": ["\\\\b([0-9]{8}[A-Za-z])\\\\b"]
                    }
                },
                "validation_rules": {},
                "referential_prompts": {}
            }
            
    def _compile_patterns(self) -> Dict[str, List]:
        """Compila patrones regex desde la configuración"""
        patterns = {}
        field_defs = self.config.get('field_definitions', {})
        
        for field, definition in field_defs.items():
            field_patterns = []
            for pattern_str in definition.get('patterns', []):
                try:
                    field_patterns.append(re.compile(pattern_str, re.IGNORECASE))
                except re.error as e:
                    print(f"Error compilando patrón {pattern_str}: {e}")
            patterns[field] = field_patterns
            
        return patterns
    
    def update(self, message: str) -> None:
        """Actualiza contexto basado en el mensaje y la configuración."""
        self.data['last_message'] = message
        
        # Solo agregar al historial si no es un duplicado
        if not self.data['conversation_history'] or self.data['conversation_history'][-1] != message:
            self.data['conversation_history'].append(message)
        
        # Extraer campos configurados (solo actualizar si se encuentra en el mensaje)
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                match = pattern.search(message)
                if match:
                    # Usar el primer grupo de captura si existe, sino el match completo
                    value = match.group(1) if match.groups() else match.group(0)
                    self.data['fields'][field] = value
                    self.data[field] = value  # También guardarlo en el nivel raíz
                    break
            # Si no se encontró el campo en este mensaje, mantener el valor anterior si existe
            # No borrar campos existentes cuando no se mencionan
        
        # Detectar tipo de query
        self._detect_query_type(message)
        
        # Detectar si es referencial
        self._detect_referential(message)
    
    def _detect_query_type(self, message: str) -> None:
        """Detecta el tipo de query basado en la configuración."""
        message_lower = message.lower()
        query_types = self.config.get('query_types', {})
        
        for query_type, keywords in query_types.items():
            if any(keyword in message_lower for keyword in keywords):
                self.data['query_type'] = query_type
                return
        
        self.data['query_type'] = 'generic'
    
    def _detect_referential(self, message: str) -> None:
        """Detecta si el mensaje es referencial basado en los indicadores configurados."""
        reference_indicators = self.config.get('reference_indicators', [])
        message_lower = message.lower()
        
        self.data['is_referential'] = any(
            indicator in message_lower for indicator in reference_indicators
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
    
    def as_dict(self) -> Dict[str, Any]:
        return self.data.copy()
    
    def validate_context(self) -> Optional[Dict[str, str]]:
        """Valida el contexto según las reglas configuradas."""
        validation_rules = self.config.get('field_rules', {})
        query_type = self.data.get('query_type', 'generic')
        
        # Obtener reglas para el tipo de query actual
        rules = validation_rules.get(query_type, {})
        required_fields = rules.get('require', [])
        
        errors = {}
        error_messages = self.config.get('error_messages', {})
        
        for field in required_fields:
            if not self.data.get(field):
                errors[field] = error_messages.get(field, f'Campo {field} requerido')
        
        return errors if errors else None
    
    def get_auto_complete_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene configuración de auto-completado para herramientas.
        Retorna un diccionario con campos que pueden ser auto-completados.
        """
        return self.config.get('auto_complete_config', {})
    
    def get_referential_prompt(self) -> Optional[str]:
        """Obtiene prompt referencial basado en la configuración."""
        if not self.data.get('is_referential'):
            return None
            
        prompts = self.config.get('referential_prompts', {})
        query_type = self.data.get('query_type', 'generic')
        
        base_prompt = prompts.get(query_type, prompts.get('default', ''))
        
        # Reemplazar variables en el prompt
        for key, value in self.data.items():
            if isinstance(value, str):
                base_prompt = base_prompt.replace(f'{{{key}}}', value)
        
        return base_prompt if base_prompt else None
