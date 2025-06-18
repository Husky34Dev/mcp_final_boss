from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger("chat_agent")

@dataclass
class ContextConfig:
    """Configuración del validador de contexto."""
    # Campos requeridos globalmente (ej: dni)
    required_fields: Set[str] = field(default_factory=lambda: {"dni"})
    
    # Palabras que indican referencias a consultas anteriores
    reference_indicators: Set[str] = field(default_factory=lambda: {
        "este", "estos", "sus", "su", "mismo", "anterior", "anteriores",
        "y ahora", "y los", "y las", "otro", "otra"
    })
    
    # Mapeo de tipos de consulta a sus palabras clave
    query_types: Dict[str, Set[str]] = field(default_factory=lambda: {
        "factura": {"factura", "pago", "deuda", "recibo", "cobro", "importe"},
        "incidencia": {"incidencia", "avería", "problema", "fallo", "error"}
    })

class ContextValidator:
    """Validador simplificado de contexto para consultas."""
    
    def __init__(self, config: Optional[ContextConfig] = None):
        """Inicializa el validador con una configuración opcional."""
        self.config = config or ContextConfig()

    def validate_dni(self, args: Dict[str, Any], context: Dict[str, Any], is_referential: bool = False) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Valida y normaliza el DNI en los argumentos.
        
        Args:
            args: Argumentos de la herramienta
            context: Contexto actual
            is_referential: Si es True, fuerza el uso del DNI del contexto
        """
        if "dni" not in args:
            return args, None
            
        # En consultas referenciales, SIEMPRE usar el DNI del contexto
        if is_referential and "dni" in context:
            args["dni"] = context["dni"]
            return args, None

        # Lista de valores inválidos a comprobar
        invalid_values = {
            "yourdni", "your_dni", "your dni", "dni", "",
            "your", "yours", "their", "his", "her",
            "{dni}", "${dni}", "$dni", "dni_value"
        }
        
        # Limpiar y normalizar primero
        dni = args["dni"].strip()
        
        # Si el DNI está vacío o contiene placeholders, usar el del contexto
        if (dni.lower() in invalid_values or 
            any(placeholder in dni.lower() for placeholder in ["your", "dni", "{", "}"])):
            if "dni" not in context:
                return args, "Se requiere un DNI válido para esta consulta."
            args["dni"] = context["dni"]
        
        # Asegurar formato correcto: 8 dígitos + letra
        if not re.match(r"^\d{8}[a-zA-Z]$", args["dni"], re.IGNORECASE):
            if "dni" in context and re.match(r"^\d{8}[a-zA-Z]$", context["dni"], re.IGNORECASE):
                args["dni"] = context["dni"]
            else:
                return args, "El formato del DNI no es válido (debe ser 8 dígitos + letra)."
        
        # Siempre convertir la letra a mayúscula
        args["dni"] = args["dni"][:-1] + args["dni"][-1].upper()
        
        # Verificar consistencia con el contexto para evitar confusiones
        if "dni" in context and args["dni"] != context["dni"]:
            logger.warning(f"[CONTEXT] Inconsistencia detectada - Argumento DNI: {args['dni']}, Contexto DNI: {context['dni']}")
            if is_referential:
                args["dni"] = context["dni"]  # En consultas referenciales, priorizar el contexto
            
        return args, None

    def is_general_query(self, message: str) -> bool:
        """Determina si es una consulta general que debería usar solo datos_abonado."""
        message_lower = message.lower()
        general_indicators = {
            "todos los datos", "datos generales", "información general",
            "datos del abonado", "información del abonado", "datos completos",
            "toda la información", "todo sobre", "datos de"
        }
        return any(indicator in message_lower for indicator in general_indicators)

    def requires_real_data(self, message: str) -> bool:
        """Determina si el mensaje requiere datos de una herramienta."""
        message_lower = message.lower()
        return (
            any(ref in message_lower for ref in self.config.reference_indicators) or
            self.is_general_query(message_lower) or
            any(any(kw in message_lower for kw in keywords) 
                for keywords in self.config.query_types.values())
        )

    def update_context(self, message: str, context: Dict[str, Any]) -> tuple[str, bool]:
        """
        Procesa un mensaje y actualiza el contexto.
        Retorna el mensaje (posiblemente modificado) y si el contexto es válido.
        """
        message_lower = message.lower()
        
        # Extraer DNI si está presente
        dni_match = re.search(r"\b\d{8}[a-zA-Z]\b", message, re.IGNORECASE)
        if dni_match:
            context["dni"] = dni_match.group(0).upper()
        
        # Detectar tipo de consulta
        query_type = None
        for tipo, keywords in self.config.query_types.items():
            if any(kw in message_lower for kw in keywords):
                query_type = tipo
                break
        
        # Para consultas referenciales, mantener el tipo anterior
        if not query_type:
            for ref in self.config.reference_indicators:
                if ref in message_lower:
                    if "query_type" in context:
                        query_type = context["query_type"]
                        # Añadir el DNI al mensaje si no está explícito
                        if "dni" in context and context["dni"] not in message:
                            message = f"{message} (DNI: {context['dni']})"
                    break
        
        # Actualizar tipo de consulta en el contexto
        if query_type:
            context["query_type"] = query_type
            
        # Verificar campos requeridos (mínimo necesario para procesar)
        if query_type or any(ref in message_lower for ref in self.config.reference_indicators):
            has_required = all(field in context for field in self.config.required_fields)
            return message, has_required
        return message, True  # Si no es consulta tipada, no requiere validación

    def is_referential_query(self, message: str) -> bool:
        """Determina si es una consulta referencial que debe mantener el DNI del contexto."""
        message_lower = message.lower()
        return (
            any(ref in message_lower for ref in self.config.reference_indicators) or
            message_lower.strip().startswith(("y ", "y,", "también ", "además ")) or
            not any(char.isdigit() for char in message_lower)  # No contiene números
        )
