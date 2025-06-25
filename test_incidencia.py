"""
Prueba completa del flujo de validación para incidencia_creacion
que requiere: dni, ubicacion, descripcion
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from framework.core.context_manager import FrameworkContextManager
from framework.core.generic_context import GenericConversationContext

def test_incidencia_creation():
    """Prueba completa de creación de incidencia con todos los campos."""
    print("🧪 Probando creación de incidencia completa...")
    
    cm = FrameworkContextManager("my_app/context_config.json")
    context = GenericConversationContext(cm)
    
    # Test: Crear incidencia con todos los campos
    print("\n📋 Test: Crear incidencia con todos los campos")
    context.update("Crear incidencia de 12345678A en Madrid, descripción: no hay internet")
    validation_result = context.validate_context()
    print(f"Contexto: {context.as_dict()}")
    print(f"Validación: {validation_result}")
    
    # Ver qué campos requiere incidencia_creacion
    required_fields = cm.get_required_fields('incidencia_creacion')
    print(f"Campos requeridos para incidencia_creacion: {required_fields}")

if __name__ == "__main__":
    test_incidencia_creation()
