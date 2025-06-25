"""
Core del Framework Multi-Agente.
"""

from .agent import BaseAgent
from .router import SimpleRouter
from .context_manager import SimpleConversationContext

__all__ = ["BaseAgent", "SimpleRouter", "SimpleConversationContext"]
