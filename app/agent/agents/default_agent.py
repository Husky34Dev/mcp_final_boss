# app/agent/default_agent.py

import re
from app.agent.chat_agent import ChatAgent  # Asegúrate de importar ChatAgent desde la ubicación correcta

class DefaultAgent:
    def __init__(self, chat_agent):
        self.prompt = (
            "Eres un asistente general para operadores de una compañía de servicios. "
            "\n\nREGLAS CRÍTICAS:"
            "\n1. NUNCA generes o inventes datos. Todos los datos deben venir de las herramientas disponibles."
            "\n2. SIEMPRE usa una herramienta cuando necesites obtener datos de un abonado, factura o incidencia."
            "\n3. Si una consulta requiere datos y no puedes obtenerlos, indica que no puedes acceder a esa información."
            "\n4. Formatea las respuestas en Markdown profesional usando títulos y listas."
            "\n5. Para datos estructurados, usa el siguiente formato abstracto:"
            "\n### [Título apropiado]"
            "\n- **[Campo]:** [Valor de la herramienta]"
            "\n- **[Campo]:** [Valor de la herramienta]"
        )        # Reutilizar la instancia de ChatAgent existente y solo actualizar el prompt
        self.agent = chat_agent
        # Actualizar el mensaje de sistema en el historial
        if self.agent.messages_history and self.agent.messages_history[0]["role"] == "system":
            self.agent.messages_history[0]["content"] = self.prompt

    def can_handle(self, message: str) -> bool:
        # Solo maneja preguntas generales o de datos personales, no de facturación ni incidencias
        return not (re.search(r"\b(factura|facturas|pago|pagos|deuda|importe|vencida|vencidas|recibo|recibos)\b", message, re.IGNORECASE) or                    re.search(r"\b(incidencia|avería|averias|reporte|problema|zona|corte|caída|caida|fallo|fallos)\b", message, re.IGNORECASE))

    def handle_message(self, message: str) -> str:
        return self.agent.handle_message_with_context(message)[0]
