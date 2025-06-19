from app.agent.agents.shared_chat_agent import SharedChatAgent
from app.agent.agents.factura_agent import FacturaAgent
from app.agent.agents.incidencia_agent import IncidenciaAgent
from app.agent.agents.default_agent import DefaultAgent

class MultiAgentRouter:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.shared_agent = SharedChatAgent(model)
        self.agents = [FacturaAgent(), IncidenciaAgent(), DefaultAgent()]

    def handle_message(self, message: str) -> str:
        for agent in self.agents:
            if agent.can_handle(message):
                self.shared_agent.set_system_prompt(agent.system_prompt())
                return self.shared_agent.handle_message_with_context(message)
        return "Lo siento, no puedo procesar tu solicitud."
