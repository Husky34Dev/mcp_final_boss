# app/agent/incidencia_agent.py
import re
from app.agent.chat_agent import ChatAgent  # Asegúrate de importar ChatAgent desde la ubicación correcta

class IncidenciaAgent:
    def __init__(self, chat_agent):
        self.prompt = (
            "Eres un asistente experto en incidencias técnicas de una compañía de servicios. "
            "\n\nREGLAS CRÍTICAS:"
            "\n1. NUNCA generes o inventes datos. Todos los datos deben venir de las herramientas disponibles."
            "\n2. SIEMPRE usa una herramienta cuando necesites obtener datos de incidencias."
            "\n3. Si una consulta requiere datos y no puedes obtenerlos, indica que no puedes acceder a esa información."
            "\n4. Formatea las respuestas en Markdown profesional."
            "\n5. Para incidencias individuales:"
            "\n### [Título apropiado]"
            "\n- **[Campo de incidencia]:** [Valor de la herramienta]"
            "\n\n6. Para múltiples incidencias, usa tablas Markdown:"
            "\n| ID | Ubicación | Estado |"
            "\n|:---|:----------|:-------|"
            "\n| [id] | [ubicación] | [estado] |"
        )
        # Crear una nueva instancia de ChatAgent con el prompt específico
        self.agent = ChatAgent(
            tools=chat_agent.tool_names,
            context=chat_agent.context,
            system_prompt=self.prompt
        )

    def can_handle(self, message: str) -> bool:
        # Solo maneja preguntas relacionadas con incidencias técnicas
        return bool(re.search(r"\b(incidencia|avería|averias|reporte|problema|zona|corte|caída|caida|fallo|fallos)\b", message, re.IGNORECASE))

    def handle_message(self, message: str) -> str:
        return self.agent.handle_message_with_context(message)[0]