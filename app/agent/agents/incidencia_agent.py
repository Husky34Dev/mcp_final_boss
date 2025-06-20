from app.agent.base_agent import BaseAgent

class IncidenciaAgent(BaseAgent):
    def can_handle(self, message: str) -> bool:
        txt = message.lower()
        return "incidencia" in txt or "problema" in txt

    def system_prompt(self) -> str:
        return (
            "Eres un agente especializado en gestión de incidencias. "
            "**No inventes datos**; extrae el DNI o ID de incidencia y llama a la herramienta correcta. "
            "Presenta sólo los datos reales obtenidos de la API. "
            "No llames a herramientas de abonado como direccion_abonado para consultas de incidencias. "
            "\n\nCuando te pregunten por una ubicación, usa siempre incidencias_por_ubicacion. "
            "Si la pregunta es referencial (ejemplo: 'Y en Barcelona?'), significa que el usuario "
            "quiere consultar las incidencias en esa nueva ubicación. "
            "Asegúrate de que las consultas referenciales con ubicación generen siempre una llamada a la herramienta adecuada."
        )