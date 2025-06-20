from app.agent.agents.shared_chat_agent import SharedChatAgent
from app.agent.agents.factura_agent import FacturaAgent
from app.agent.agents.incidencia_agent import IncidenciaAgent
from app.agent.agents.default_agent import DefaultAgent

class MultiAgentRouter:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.shared_agent = SharedChatAgent(model)
        self.agents = [FacturaAgent(), IncidenciaAgent(), DefaultAgent()]

    def handle_message(self, message: str) -> str:
        query_type = self.shared_agent.context.get('query_type')

        if query_type == 'incidencia':
            agent = IncidenciaAgent()
        elif query_type == 'factura':
            agent = FacturaAgent()
        else:
            # Fallback por keywords si query_type no está definido
            for ag in self.agents:
                if ag.can_handle(message):
                    agent = ag
                    break
            else:
                agent = DefaultAgent()

        self.shared_agent.set_system_prompt(agent.system_prompt())
        return self.shared_agent.handle_message_with_context(message)
