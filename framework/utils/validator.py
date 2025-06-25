"""
Validador centralizado para campos comunes del framework.
Evita duplicación de lógica de validación.
"""
import re
from typing import Dict, List, Optional


class FrameworkValidator:
    """Validador centralizado para campos comunes."""
    
    # Patrones de validación centralizados
    PATTERNS = {
        'dni_spain': r'^\d{8}[A-Za-z]$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone_spain': r'^(\+34|0034|34)?[6789]\d{8}$'
    }
    
    @classmethod
    def validate_dni(cls, dni: str) -> bool:
        """Valida DNI español."""
        if not dni:
            return False
        return bool(re.match(cls.PATTERNS['dni_spain'], dni.strip()))
    
    @classmethod
    def validate_field(cls, field_type: str, value: str) -> bool:
        """Valida un campo según su tipo."""
        if not value:
            return False
            
        pattern = cls.PATTERNS.get(field_type)
        if not pattern:
            return True  # Si no hay patrón, aceptar
            
        return bool(re.match(pattern, value.strip()))
    
    @classmethod
    def get_validation_error(cls, field_type: str) -> str:
        """Obtiene mensaje de error para un tipo de campo."""
        messages = {
            'dni_spain': 'DNI debe tener formato 12345678A (8 dígitos + 1 letra)',
            'email': 'Email debe tener formato válido',
            'phone_spain': 'Teléfono debe ser válido para España'
        }
        return messages.get(field_type, f'Campo {field_type} no válido')
