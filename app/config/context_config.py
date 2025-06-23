from dataclasses import dataclass, field
from typing import Dict, List, Pattern, Optional, Set, Any
import re
import json

@dataclass
class ContextFieldDefinition:
    """Define las características de un campo de contexto"""
    name: str
    patterns: List[Pattern]
    required_for: List[str]  # Lista de tipos de consulta donde este campo es requerido
    description: str
    validation_func: Optional[callable] = None

class ContextManager:
    """
    Gestor centralizado de contexto: maneja la configuración, extracción y validación.
    Esta clase une las responsabilidades de configuración y validación para simplificar
    la arquitectura.
    """
    
    def __init__(self):
        # Cargar configuración desde archivo JSON
        with open("c:\\projects\\mcp_groq\\app\\config\\query_config.json", "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        self.query_types = config["query_types"]
        self.action_verbs = config["action_verbs"]
        self.reference_indicators = set(config["reference_indicators"])
        self.no_data_indicators = set(config["no_data_indicators"])
        self.real_data_required = set(config["real_data_required"])
        self.field_rules = config["field_rules"]

        self._initialize_fields()

    def _initialize_fields(self):
        """Inicializa la definición de campos y sus patrones desde query_config.json"""
        with open("c:\\projects\\mcp_groq\\app\\config\\query_config.json", "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        field_definitions = config.get("field_definitions", {})

        def validate_dni(dni: str) -> bool:
            if not dni:
                return False
            return bool(re.match(r'^\d{8}[A-Za-z]$', dni))

        self.fields = {}
        for field_name, field_config in field_definitions.items():
            patterns = [re.compile(pattern, re.IGNORECASE) for pattern in field_config.get("patterns", [])]
            required_for = field_config.get("required_for", [])
            description = field_config.get("description", "")
            validation_func = validate_dni if field_name == "dni" else None

            self.fields[field_name] = ContextFieldDefinition(
                name=field_name,
                patterns=patterns,
                required_for=required_for,
                description=description,
                validation_func=validation_func
            )
    
    def detect_query_type(self, text: str) -> str:
        """
        Detecta el tipo de consulta usando una combinación de palabras clave y análisis contextual.
        """
        text_lower = text.lower()
        words = text_lower.split()

        detection_logic = {
            "question_starters": self.query_types.get("question_starters", []),
            "referential_phrases": self.query_types.get("referential_phrases", []),
            "creation_triggers": self.query_types.get("creation_triggers", []),
        }

        # Detectar consultas basadas en verbos de acción explícitos
        for query_type, verbs in self.action_verbs.items():
            if any(verb in words for verb in verbs):
                return query_type

        # Detectar consultas basadas en estructura de pregunta
        question_starters = detection_logic.get("question_starters", [])
        if any(text_lower.startswith(starter) for starter in question_starters):
            if "incidencia" in text_lower:
                return "incidencia_consulta"
            if any(word in text_lower for word in self.query_types.get("factura", [])):
                return "factura"

        # Detectar consultas por frases referenciales
        referential_phrases = detection_logic.get("referential_phrases", [])
        if any(phrase in text_lower for phrase in referential_phrases):
            return "incidencia_consulta"

        creation_triggers = detection_logic.get("creation_triggers", [])
        if any(word in text_lower for word in creation_triggers):
            return "incidencia_creacion"

        if ":" in text or "porque" in text_lower or "ya que" in text_lower:
            return "incidencia_creacion"

        # Detectar consultas basadas en palabras clave
        for query_type, keywords in self.query_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return query_type

        return "unknown"
        
    def get_required_fields(self, query_type: str) -> List[str]:
        """Retorna la lista de campos requeridos para un tipo de consulta específico"""
        required_fields = []
        for field_name, field_def in self.fields.items():
            if query_type in field_def.required_for:
                required_fields.append(field_name)
        return required_fields

    def extract_field(self, field_name: str, text: str) -> Optional[str]:
        """
        Extrae el valor de un campo del texto usando patrones o inferencia contextual.
        Primero intenta con patrones explícitos, luego usa heurísticas contextuales.
        """
        if field_name not in self.fields:
            return None
            
        field = self.fields[field_name]
        
        # 1. Intenta con patrones explícitos primero
        for pattern in field.patterns:
            match = pattern.search(text)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                return value.strip()
        
        # 2. Si los patrones fallan, no inferimos valores para ubicacion ni descripcion
        return None

    def validate_context(self, context: dict) -> List[str]:
        """
        Valida que el contexto tenga todos los campos requeridos según el tipo de consulta.
        
        Args:
            context: Diccionario con el contexto actual
            
        Returns:
            Lista de nombres de campos faltantes o con formato inválido
        """
        query_type = context.get('query_type', 'unknown')
        if query_type == 'unknown':
            return ["tipo_consulta"]
            
        missing_fields = []
        required_fields = self.get_required_fields(query_type)
        
        for field_name in required_fields:
            field_value = context.get(field_name)
            
            if not field_value:
                missing_fields.append(field_name)
                continue
                
            field_def = self.fields.get(field_name)
            if field_def and field_def.validation_func:
                if not field_def.validation_func(field_value):
                    missing_fields.append(f"{field_name} (formato inválido)")
                
        return missing_fields

    def is_referential_query(self, text: str) -> bool:
        """
        Determina si una consulta hace referencia a contexto anterior.
        """
        text_lower = text.lower()
        # Si se especifica un DNI explícito, no es referencial
        if re.search(r"\b[0-9]{8}[A-Z]\b", text):
            return False
        # Si solicita 'otro' o 'otra' entidad (no temporal 'otra vez'), no es consulta referencial
        non_ref = re.search(r"\botro\s+\w+", text_lower) or re.search(r"\botra\s+\w+", text_lower)
        if non_ref and 'otra vez' not in text_lower:
            return False
        # Verifica si el texto contiene alguno de los indicadores de referencia
        return any(indicator in text_lower for indicator in self.reference_indicators)

    def requires_real_data(self, text: str) -> bool:
        """
        Determina si una consulta requiere datos reales de la API.
        
        Args:
            text: El mensaje del usuario
            
        Returns:
            True si la consulta necesita datos reales, False si puede ser respondida sin datos
        """
        text_lower = text.lower()
        
        # Si contiene indicadores de consulta informativa, no requiere datos reales
        if any(indicator in text_lower for indicator in self.no_data_indicators):
            return False
            
        # Detectar el tipo de consulta
        query_type = self.detect_query_type(text)
        
        # Verificar si el tipo de consulta requiere datos reales
        return query_type in self.real_data_required

    def get_field_rules(self, query_type: str) -> Optional[Dict[str, List[str]]]:
        """
        Devuelve las reglas de herencia y eliminación de campos para un tipo de consulta.
        """
        return self.field_rules.get(query_type, None)

# Crear una instancia global del ContextManager
context_config = ContextManager()
