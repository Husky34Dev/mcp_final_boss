"""
Test rápido para verificar que la detección de referencialidad funciona correctamente.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from framework.core.context_manager import FrameworkContextManager
from framework.core.generic_context import GenericConversationContext

def test_referential_detection():
    """Prueba la detección de referencialidad corregida."""
    print("🧪 Probando detección de referencialidad...")
    
    cm = FrameworkContextManager("my_app/context_config.json")
    context = GenericConversationContext(cm)
    
    # Test 1: Mensaje con DNI explícito (NO referencial)
    print("\n📋 Test 1: Mensaje con DNI explícito")
    context.update("Dame los datos del abonado 12345678A")
    print(f"Query type: {context.get('query_type')}")
    print(f"Is referential: {context.get('is_referential')}")  # Debería ser False
    print(f"DNI extraído: {context.get('dni')}")
    
    # Test 2: Mensaje referencial (sin DNI)
    print("\n📋 Test 2: Mensaje referencial")
    context.update("¿Y sus datos?")
    print(f"Query type: {context.get('query_type')}")
    print(f"Is referential: {context.get('is_referential')}")  # Debería ser True
    print(f"DNI heredado: {context.get('dni')}")

if __name__ == "__main__":
    test_referential_detection()
