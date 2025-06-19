from app.agent.base_agent import BaseAgent

class DefaultAgent(BaseAgent):
    def can_handle(self, message: str) -> bool:
        return True

    def system_prompt(self) -> str:
        return (
            "Eres un asistente general. Responde preguntas comunes sin inventar datos. "
            "Si no aplican herramientas específicas, responde con conocimiento general."
        )
