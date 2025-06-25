"""
Paquete de la aplicación multi-agente para telecomunicaciones.

Este paquete contiene:
- Configuración principal del sistema (app_config.py)
- Configuración de agentes especializados (agents_config.json)
- Configuración de contexto y detección de queries (context_config.json)

Uso:
    from my_app.app_config import handle_chat_message
    
    response = handle_chat_message("¿Cuáles son mis facturas?")
"""

from .app_config import handle_chat_message, get_router, preload_all_tools

__version__ = "1.0.0"
__all__ = ["handle_chat_message", "get_router", "preload_all_tools"]
