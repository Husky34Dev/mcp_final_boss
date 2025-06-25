"""
Framework Multi-Agente Configurable por JSON
============================================

Un framework simple y limpio para crear sistemas multi-agente configurables.

Componentes principales:
- core.agent: Agente base reutilizable  
- core.context: Manejo de contexto configurable por JSON
- core.router: Router simple para dirigir mensajes a agentes
- tools: Herramientas para OpenAPI y formateo
- utils: Utilidades como guardián de respuestas y handler de funciones
"""

from .core.agent import BaseAgent
from .core.router import SimpleRouter

__version__ = "1.0.0"
__all__ = ["BaseAgent", "SimpleRouter"]
