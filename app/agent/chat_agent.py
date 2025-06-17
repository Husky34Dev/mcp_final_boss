# app/agent/chat_agent.py

from app.agent.chat_core import ChatAgent
from app.agent.agents.factura_agent import FacturaAgent
from app.agent.agents.incidencia_agent import IncidenciaAgent
from app.agent.agents.default_agent import DefaultAgent
from app.agent.roles import ROLES_TOOLS

class MultiAgentRouter:
    def __init__(self, role="admin"):
        allowed_tools = ROLES_TOOLS.get(role, [])
        self.shared_agent = ChatAgent(tools=allowed_tools)
        
        # Inicializar los agentes especializados
        self.factura_agent = FacturaAgent(self.shared_agent)
        self.incidencia_agent = IncidenciaAgent(self.shared_agent)
        self.default_agent = DefaultAgent(self.shared_agent)

    def handle_message(self, message: str) -> str:
        # Primero intentar con los can_handle de cada agente especializado
        if self.factura_agent.can_handle(message):
            return self.factura_agent.handle_message(message)
        elif self.incidencia_agent.can_handle(message):
            return self.incidencia_agent.handle_message(message)

        # Si ningún agente especializado lo maneja, usar el default
        return self.default_agent.handle_message(message)
