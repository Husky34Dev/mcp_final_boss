from app.agent.agents.shared_chat_agent import SharedChatAgent
from app.agent.agents.factura_agent import FacturaAgent
from app.agent.agents.incidencia_agent import IncidenciaAgent
from app.agent.agents.default_agent import DefaultAgent
from app.config.config import MODEL
from app.config.context_config import context_config  # para detectar tipo de consulta

class MultiAgentRouter:
    def __init__(self, model: str = MODEL):
        self.shared_agent = SharedChatAgent(model)
        self.agents = [FacturaAgent(), IncidenciaAgent(), DefaultAgent()]

    def handle_message(self, message: str) -> str:
        # Detectar tipo de consulta fresca desde el mensaje
        fresh_qt = context_config.detect_query_type(message)
        # Si no se detecta y es referencial, usar tipo almacenado en contexto
        if fresh_qt == 'unknown' and self.shared_agent.context.get('is_referential'):
            query_type = self.shared_agent.context.get('query_type', 'unknown')
        else:
            query_type = fresh_qt

        # Set `force_tool_usage` for specific agents
        if query_type.startswith('incidencia'):
            agent = IncidenciaAgent()
            self.shared_agent.force_tool_usage = True
        elif query_type == 'factura':
            agent = FacturaAgent()
            self.shared_agent.force_tool_usage = True
        else:
            # Default behavior
            self.shared_agent.force_tool_usage = True
            for ag in self.agents:
                if ag.can_handle(message):
                    agent = ag
                    break
            else:
                agent = DefaultAgent()

        self.shared_agent.set_system_prompt(agent.system_prompt())
        return self.shared_agent.handle_message_with_context(message)
