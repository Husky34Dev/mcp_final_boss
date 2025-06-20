from dataclasses import dataclass, field
from typing import Dict, List, Pattern, Optional, Set, Any
import re

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
        # Campos y sus definiciones
        self.fields: Dict[str, ContextFieldDefinition] = {}
        
        # Palabras clave para detectar consultas referenciales
        self.reference_indicators: Set[str] = {
            "este", "estos", "sus", "su", "mismo", "anterior", "anteriores",
            "y ahora", "y los", "y las", "otro", "otra", "y en"
        }
        
        # Tipos de consulta y sus palabras clave
        self.query_types: Dict[str, Set[str]] = {
            "factura": {"factura", "pago", "deuda", "recibo", "cobro", "importe"},
            "incidencia_consulta": {
                "hay incidencias", "existen incidencias", "mostrar incidencias", 
                "listar incidencias", "ver incidencias", "muestra mis incidencias",
                "mis incidencias", "consultar incidencias", "consulta incidencias"
            },
            "incidencia_creacion": {"reportar incidencia", "crear incidencia", "registrar incidencia", "nueva incidencia"},
            "abonado": {"abonado", "datos de abonado", "datos del abonado", "información del abonado"}
        }
        
        # Tipos de consulta que requieren datos reales
        self.real_data_required: Set[str] = {
            "factura", 
            "incidencia_consulta", 
            "incidencia_creacion", 
            "abonado"
        }
        
        # Indicadores de que una consulta puede ser respondida sin datos reales
        self.no_data_indicators: Set[str] = {
            "cómo", "como", "qué es", "que es", "explica", 
            "ayuda", "ejemplo", "manual", "instrucciones"
        }
        
        self._initialize_fields()

    def _initialize_fields(self):
        """Inicializa la definición de campos y sus patrones"""
        
        def validate_dni(dni: str) -> bool:
            if not dni:
                return False
            return bool(re.match(r'^\d{8}[A-Z]$', dni))
            
        self.fields = {
            'dni': ContextFieldDefinition(
                name='dni',
                patterns=[
                    re.compile(r'\b[0-9]{8}[A-Z]\b', re.IGNORECASE),  # DNI español
                    re.compile(r'dni:?\s*([0-9]{8}[A-Z])', re.IGNORECASE)
                ],
                required_for=['abonado', 'factura', 'incidencia_creacion', 'incidencia_consulta'],
                description='DNI del cliente',
                validation_func=validate_dni
            ),
            'ubicacion': ContextFieldDefinition(
                name='ubicacion',
                patterns=[
                    re.compile(r'(?:en|de)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s*(?:,|\.|$|dni|descripci[oó]n))'),
                    re.compile(r'ubicaci[oó]n:?\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s*(?:,|\.|$|dni|descripci[oó]n))')
                ],
                required_for=['incidencia_creacion'],  # Solo requerido para creación
                description='Ubicación para consultas de incidencias'
            ),
            'descripcion': ContextFieldDefinition(
                name='descripcion',
                patterns=[
                    re.compile(r'descripci[oó]n:?\s+(.+?)(?:\s*(?:,|\.|$))'),
                    re.compile(r'(?:[:,]\s*)([^,\.]+?)(?:\s*(?:,|\.|$))')  # Captura texto después de : o , hasta el siguiente separador
                ],
                required_for=['incidencia_creacion'],
                description='Descripción de la incidencia'
            ),
            'fecha': ContextFieldDefinition(
                name='fecha',
                patterns=[
                    re.compile(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'),
                    re.compile(r'fecha:?\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})')
                ],
                required_for=[],  # Opcional para todos los tipos
                description='Fecha para filtrar consultas'
            )
        }
    
    def detect_query_type(self, text: str) -> str:
        """
        Detecta el tipo de consulta usando una combinación de palabras clave y análisis contextual.
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        # Primero detectar consultas basadas en verbos de acción explícitos
        action_verbs = {
            'incidencia_creacion': {'reportar', 'crear', 'registrar', 'abrir', 'nueva'},
            'incidencia_consulta': {'ver', 'mostrar', 'listar', 'buscar', 'muestra', 'consultar', 'consulta'},
            'factura': {'pagar', 'abonar', 'facturar', 'cobrar'}
        }
        
        for query_type, verbs in action_verbs.items():
            if any(verb in words for verb in verbs):
                return query_type
        
        # Detectar consultas basadas en estructura de pregunta
        if text_lower.startswith(('hay', 'existen', 'cuántas', 'cuantas', 'qué', 'que', 'lista', 'listar', 'muestra', 'mostrar')):
            if 'incidencia' in text_lower:
                return "incidencia_consulta"
            if any(word in text_lower for word in ['factura', 'pago', 'deuda']):
                return "factura"
        
        # Detectar consultas por DNI o por abonado
        if 'incidencia' in text_lower or 'incidencias' in text_lower:
            # Si es una consulta por DNI o abonado, es una consulta no creación
            if any(phrase in text_lower for phrase in [
                'del abonado', 'de abonado', 'del dni', 'con dni', 'por dni',
                'asociadas al', 'asociadas a', 'relacionadas con'
            ]):
                return "incidencia_consulta"
            
            # Si tiene indicadores explícitos de creación
            if any(word in text_lower for word in ['tengo', 'quiero reportar', 'quiero crear', 'hay que', 'necesito crear']):
                return "incidencia_creacion"
            
            # Si tiene una descripción después de dos puntos o con un "porque", es probablemente creación
            if ':' in text or 'porque' in text_lower or 'ya que' in text_lower:
                return "incidencia_creacion"
                
            # Por defecto, si no hay indicadores claros, asumir consulta
            return "incidencia_consulta"
            
        # Inferir por presencia de palabras clave en cualquier parte
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
        
        # 2. Si los patrones fallan, usa heurísticas contextuales
        text_lower = text.lower()
        if field_name == 'ubicacion':
            # Para ubicación, busca nombres propios después de preposiciones comunes
            locations = re.finditer(r'(?:en|de|para|sobre|desde|hacia)\s+([A-Z][a-záéíóúñ]+)', text)
            for match in locations:
                return match.group(1)
                
            # También busca cualquier palabra capitalizada que no sea inicio de frase
            locations = re.finditer(r'(?<!\.)\s+([A-Z][a-záéíóúñ]+)', text)
            for match in locations:
                return match.group(1)
                
        elif field_name == 'descripcion':
            # Para descripción, si hay dos puntos, toma todo lo que sigue
            if ':' in text:
                return text.split(':', 1)[1].strip()
            # O toma todo después de palabras clave comunes
            for trigger in ['porque', 'ya que', 'debido a']:
                if trigger in text_lower:
                    return text_lower.split(trigger, 1)[1].strip()
                    
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
        
        Args:
            text: El mensaje del usuario
            
        Returns:
            True si la consulta es referencial (usa pronombres o referencias a contexto anterior),
            False si es una consulta independiente
        """
        text_lower = text.lower()
        
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

    def extract_query_type(self, text: str) -> str:
        """
        Alias para detect_query_type para mantener compatibilidad con código existente.
        """
        return self.detect_query_type(text)

# Crear una instancia global del ContextManager
context_config = ContextManager()
