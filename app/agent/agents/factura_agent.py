from app.agent.base_agent import BaseAgent

class FacturaAgent(BaseAgent):
    def can_handle(self, message: str) -> bool:
        txt = message.lower()
        return "factura" in txt or "facturas" in txt

    def system_prompt(self) -> str:
        return (
            "Eres un agente especializado en gestión de facturas. "
            "**No inventes datos**; utiliza herramientas para obtener información precisa. "
            "Si el usuario proporciona un DNI o ID de factura, llama a la herramienta correspondiente. "
            "Responde únicamente con los datos devueltos por la API en un formato claro y estructurado. "
            "Si no puedes encontrar datos, informa al usuario de manera transparente."
        )