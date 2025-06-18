# app/agent/factura_agent.py
import re
from app.agent.chat_agent import ChatAgent  # Asegúrate de importar ChatAgent desde la ubicación correcta

class FacturaAgent:
    def __init__(self, chat_agent):
        self.prompt = (
            "Eres un asistente especializado en facturación de una compañía de servicios. "
            "\n\nREGLAS CRÍTICAS:"
            "\n1. NUNCA generes o inventes datos. Todos los datos deben venir de las herramientas disponibles."
            "\n2. SIEMPRE usa una herramienta cuando necesites obtener datos de facturas, pagos o deudas."
            "\n3. Si una consulta requiere datos y no puedes obtenerlos, indica que no puedes acceder a esa información."
            "\n4. Formatea las respuestas en Markdown profesional."
            "\n5. Para facturas individuales:"
            "\n### [Título apropiado]"
            "\n- **[Campo de factura]:** [Valor de la herramienta]"
            "\n\n6. Para múltiples facturas, usa tablas Markdown:"
            "\n| Fecha | Estado | Importe |"
            "\n|:------|:-------|--------:|"
            "\n| [fecha] | [estado] | [importe] |"
            "\n\n7. Siempre muestra importes con dos decimales y el símbolo €"
        )
        # Crear una nueva instancia de ChatAgent con el prompt específico
        self.agent = ChatAgent(
            tools=chat_agent.tool_names,
            context=chat_agent.context,
            system_prompt=self.prompt
        )

    def can_handle(self, message: str) -> bool:
        # Solo maneja preguntas explícitas sobre facturas, pagos o deudas
        return bool(re.search(r"\b(factura|facturas|pago|pagos|deuda|importe|vencida|vencidas|recibo|recibos)\b", message, re.IGNORECASE))

    def handle_message(self, message: str) -> str:
        return self.agent.handle_message_with_context(message)[0]
