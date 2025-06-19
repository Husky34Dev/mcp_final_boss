"""
ContextValidator: utilidades mínimas para validar si una consulta requiere datos reales o es referencial.
Archivo simplificado y preparado para ser ampliado si se requiere.
"""
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
import re

@dataclass
class ContextConfig:
    required_fields: Set[str] = field(default_factory=lambda: {"dni"})
    reference_indicators: Set[str] = field(default_factory=lambda: {
        "este", "estos", "sus", "su", "mismo", "anterior", "anteriores",
        "y ahora", "y los", "y las", "otro", "otra"
    })
    query_types: Dict[str, Set[str]] = field(default_factory=lambda: {
    "factura": {"factura", "pago", "deuda", "recibo", "cobro", "importe"},
    "incidencia": {"incidencia", "avería", "problema", "fallo", "error"},
    "abonado": {"abonado", "datos de abonado", "datos del abonado", "información del abonado"}
})

class ContextValidator:
    def __init__(self, config: Optional[ContextConfig] = None):
        self.config = config or ContextConfig()

    def requires_real_data(self, message: str) -> bool:
        """
        Determina si el mensaje requiere datos de una herramienta (API).
        """
        message_lower = message.lower()
        return (
            any(ref in message_lower for ref in self.config.reference_indicators) or
            any(any(kw in message_lower for kw in keywords)
                for keywords in self.config.query_types.values())
        )

    def is_referential_query(self, message: str) -> bool:
        """
        Determina si es una consulta referencial (depende de contexto anterior).
        """
        message_lower = message.lower()
        return any(ref in message_lower for ref in self.config.reference_indicators)
