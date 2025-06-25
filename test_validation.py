"""
Script de prueba para verificar la integración del sistema de validación.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from framework.core.context_manager import FrameworkContextManager
from framework.core.generic_context import GenericConversationContext

def test_validation_integration():
    """Prueba la integración del sistema de validación."""
    print("🧪 Probando integración del sistema de validación...")
    
    # Test 1: Consulta de factura sin DNI
    print("\n📋 Test 1: Consulta de factura sin DNI")
    cm1 = FrameworkContextManager("my_app/context_config.json")
    context1 = GenericConversationContext(cm1)
    context1.update("¿Cuáles son mis facturas?")
    validation_result = context1.validate_context()
    print(f"Contexto: {context1.as_dict()}")
    print(f"Validación: {validation_result}")
    
    # Test 2: Consulta de factura con DNI válido
    print("\n📋 Test 2: Consulta de factura con DNI válido")
    cm2 = FrameworkContextManager("my_app/context_config.json")
    context2 = GenericConversationContext(cm2)
    context2.update("¿Cuáles son las facturas de 12345678A?")
    validation_result = context2.validate_context()
    print(f"Contexto: {context2.as_dict()}")
    print(f"Validación: {validation_result}")
    
    # Test 3: DNI con formato inválido
    print("\n📋 Test 3: DNI con formato inválido")
    cm3 = FrameworkContextManager("my_app/context_config.json")
    context3 = GenericConversationContext(cm3)
    context3.update("¿Cuáles son las facturas de 123456?")
    validation_result = context3.validate_context()
    print(f"Contexto: {context3.as_dict()}")
    print(f"Validación: {validation_result}")
    
    # Test 4: Crear incidencia sin todos los campos
    print("\n📋 Test 4: Crear incidencia sin todos los campos")
    cm4 = FrameworkContextManager("my_app/context_config.json")
    context4 = GenericConversationContext(cm4)
    context4.update("Crear incidencia nueva en Madrid")
    validation_result = context4.validate_context()
    print(f"Contexto: {context4.as_dict()}")
    print(f"Validación: {validation_result}")

if __name__ == "__main__":
    test_validation_integration()
