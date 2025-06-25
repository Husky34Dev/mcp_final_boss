import json
import re
from dataclasses import dataclass
from typing import Dict, List, Pattern, Optional, Callable

@dataclass
class FieldDefinition:
    name: str
    patterns: List[Pattern]
    required_for: List[str]
    description: str
    validation_func: Optional[Callable[[str], bool]] = None

class FrameworkContextManager:
    """
    Manager centralizado de contexto usando un framework de configuración.
    Carga la configuración y ofrece métodos de extracción y validación.
    """
    def __init__(self, config_path: str):
        # Carga configuración desde JSON externo
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.query_types = config.get('query_types', {})
        self.action_verbs = config.get('action_verbs', {})
        self.reference_indicators = set(config.get('reference_indicators', []))
        self.no_data_indicators = set(config.get('no_data_indicators', []))
        self.real_data_required = set(config.get('real_data_required', []))
        self.field_rules = config.get('field_rules', {})
        self.fields: Dict[str, FieldDefinition] = {}
        self._init_fields(config)

    def _init_fields(self, config: Dict):
        """Inicializa campos con patrones y validaciones desde configuración."""
        definitions = config.get('field_definitions', {})
        error_messages = config.get('error_messages', {})
        
        for name, info in definitions.items():
            patterns = [re.compile(p, re.IGNORECASE) for p in info.get('patterns', [])]
            
            # Crear función de validación genérica desde JSON
            validation = self._create_validation_func(name, info)
            
            self.fields[name] = FieldDefinition(
                name=name,
                patterns=patterns,
                required_for=info.get('required_for', []),
                description=info.get('description', ''),
                validation_func=validation
            )
        
        # Guardar mensajes de error para uso en validación
        self.error_messages = error_messages

    def _create_validation_func(self, field_name: str, field_info: Dict):
        """
        Crea función de validación desde configuración JSON.
        Más flexible que hardcodear solo DNI.
        """
        validation_pattern = field_info.get('validation_pattern')
        if validation_pattern:
            # Validación genérica por regex desde JSON
            def validate_field(value: str) -> bool:
                return bool(re.match(validation_pattern, value.strip()))
            return validate_field
        
        # Fallback para compatibilidad: validaciones específicas conocidas
        if field_name == 'dni':
            def validate_dni(d: str) -> bool:
                return bool(re.match(r'^\d{8}[A-Za-z]$', d.strip()))
            return validate_dni
            
        return None

    def detect_query_type(self, text: str) -> str:
        text_lower = text.lower()
        words = text_lower.split()
        # verificación simplificada usando action_verbs
        for qtype, verbs in self.action_verbs.items():
            if any(verb in words for verb in verbs):
                return qtype
        # fallback básico
        for qtype, keywords in self.query_types.items():
            if any(k in text_lower for k in keywords):
                return qtype
        return 'unknown'

    def get_required_fields(self, qtype: str) -> List[str]:
        """
        Obtiene campos requeridos para un tipo de query.
        Usa field_rules como fuente de verdad.
        """
        rules = self.field_rules.get(qtype, {})
        return rules.get('require', [])

    def extract_field(self, name: str, text: str) -> Optional[str]:
        field = self.fields.get(name)
        if not field:
            return None
        for pat in field.patterns:
            m = pat.search(text)
            if m:
                return (m.group(1) if m.groups() else m.group(0)).strip()
        return None

    def validate_context(self, context: Dict[str, str]) -> List[str]:
        """
        Valida contexto y retorna lista de campos con problemas.
        Ahora usa los mensajes de error configurados en JSON.
        """
        qtype = context.get('query_type', 'unknown')
        if qtype == 'unknown':
            return ['tipo_consulta']
            
        missing = []
        for name in self.get_required_fields(qtype):
            val = context.get(name)
            if not val:
                # Usar mensaje de error personalizado si está disponible
                error_msg = self.error_messages.get(name, f"Campo {name} requerido")
                missing.append(error_msg)
            else:
                field = self.fields.get(name)
                if field and field.validation_func and not field.validation_func(val):
                    # Mensaje específico para formato inválido
                    error_msg = self.error_messages.get(
                        f"{name}_invalid", 
                        f"{name} (formato inválido)"
                    )
                    missing.append(error_msg)
        return missing

    def is_referential(self, text: str) -> bool:
        """
        Determina si un texto es referencial (se refiere a contexto previo).
        
        Un texto es referencial si:
        1. Contiene indicadores referenciales ("este", "sus", etc.)
        2. NO contiene datos explícitos nuevos (como DNI completo)
        
        Ejemplo:
        - "¿Cuáles son sus facturas?" → True (referencial)
        - "Facturas de 12345678A" → False (datos explícitos)
        - "¿Y las de Barcelona?" → True (referencial)
        """
        lower = text.lower()
        
        # Si contiene indicadores referenciales, es referencial
        if any(ind in lower for ind in self.reference_indicators):
            return True
            
        # Si contiene DNI completo, NO es referencial (datos explícitos)
        if re.search(r"\b\d{8}[A-Za-z]\b", text):
            return False
            
        return False

    def requires_real_data(self, text: str) -> bool:
        if any(ind in text.lower() for ind in self.no_data_indicators):
            return False
        return self.detect_query_type(text) in self.real_data_required

    def get_field_rules(self, qtype: str):
        return self.field_rules.get(qtype)
