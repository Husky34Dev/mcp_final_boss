"""
Core del Framework Multi-Agente.
"""

from .agent import BaseAgent
from .context import SimpleContext, ConfigurableContext  
from .router import SimpleRouter

__all__ = ["BaseAgent", "SimpleContext", "ConfigurableContext", "SimpleRouter"]
