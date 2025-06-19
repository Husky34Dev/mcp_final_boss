from app.agent.base_agent import BaseAgent

class IncidenciaAgent(BaseAgent):
    def can_handle(self, message: str) -> bool:
        txt = message.lower()
        return "incidencia" in txt or "problema" in txt

    def system_prompt(self) -> str:
        return (
            "Eres un agente especializado en gestión de incidencias. "
            "**No inventes datos**; extrae el DNI o ID de incidencia y llama a la herramienta correcta. "
            "Presenta sólo los datos reales obtenidos de la API."
        )