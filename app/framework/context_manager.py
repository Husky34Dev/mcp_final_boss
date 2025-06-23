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
        definitions = config.get('field_definitions', {})
        for name, info in definitions.items():
            patterns = [re.compile(p, re.IGNORECASE) for p in info.get('patterns', [])]
            validation = None
            if name == 'dni':
                def check(d): return bool(re.match(r'^\d{8}[A-Za-z]$', d))
                validation = check
            self.fields[name] = FieldDefinition(
                name=name,
                patterns=patterns,
                required_for=info.get('required_for', []),
                description=info.get('description', ''),
                validation_func=validation
            )

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
        return [f.name for f in self.fields.values() if qtype in f.required_for]

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
        qtype = context.get('query_type', 'unknown')
        if qtype == 'unknown':
            return ['tipo_consulta']
        missing = []
        for name in self.get_required_fields(qtype):
            val = context.get(name)
            if not val:
                missing.append(name)
            else:
                field = self.fields.get(name)
                if field and field.validation_func and not field.validation_func(val):
                    missing.append(f"{name} (formato inválido)")
        return missing

    def is_referential(self, text: str) -> bool:
        if re.search(r"\b\d{8}[A-Z]\b", text):
            return False
        lower = text.lower()
        if any(ind in lower for ind in self.reference_indicators):
            return True
        return False

    def requires_real_data(self, text: str) -> bool:
        if any(ind in text.lower() for ind in self.no_data_indicators):
            return False
        return self.detect_query_type(text) in self.real_data_required

    def get_field_rules(self, qtype: str):
        return self.field_rules.get(qtype)
