# app/agent/chat_agent.py

from app.agent.chat_core import ChatAgent
from app.agent.factura_agent import FacturaAgent
from app.agent.incidencia_agent import IncidenciaAgent
from app.agent.default_agent import DefaultAgent

class MultiAgentRouter:
    def __init__(self):
        shared_agent = ChatAgent()
        self.agents = [
            FacturaAgent(shared_agent),
            IncidenciaAgent(shared_agent),
        ]
        self.default_agent = DefaultAgent(shared_agent)

    def handle_message(self, message: str) -> str:
        for agent in self.agents:
            if agent.can_handle(message):
                return agent.handle_message(message)
        return self.default_agent.handle_message(message)
