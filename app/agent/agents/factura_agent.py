from app.agent.base_agent import BaseAgent

class FacturaAgent(BaseAgent):
    def can_handle(self, message: str) -> bool:
        txt = message.lower()
        return "factura" in txt or "facturas" in txt

    def system_prompt(self) -> str:
        return (
            "Eres un agente especializado en gestión de facturas. "
            "**No inventes datos**; extrae el DNI o ID de factura y llama a la herramienta correcta. "
            "Muestra únicamente los resultados devueltos por la API en formato claro."
        )