"""
Core del Framework Multi-Agente.
"""

from .agent import BaseAgent
from .router import SimpleRouter
from .context_manager import FrameworkContextManager
from .generic_context import GenericConversationContext

__all__ = ["BaseAgent", "SimpleRouter", "FrameworkContextManager", "GenericConversationContext"]
