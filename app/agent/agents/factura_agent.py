# app/agent/factura_agent.py
import re

class FacturaAgent:
    def __init__(self, chat_agent):
        self.agent = chat_agent
        self.prompt = (
            "Eres un asistente especializado en facturación. "
            "Responde exclusivamente a preguntas sobre facturas, pagos y deudas. "
            "Genera respuestas claras, concisas y bien estructuradas usando Markdown. "
            "Adapta el formato según el tipo de consulta: usa títulos, listas o tablas según corresponda. "
            "Si se trata de múltiples facturas o importes, muestra los datos en una tabla Markdown con columnas alineadas. "
            "Al final, incluye totales o resúmenes destacados en negrita si aplica.\n\n"
            "Ejemplos de formato:\n\n"
            "### Factura individual\n"
            "- **Número de factura:** 123456\n"
            "- **Fecha de emisión:** 01/06/2025\n"
            "- **Importe:** 120,50 €\n"
            "- **Estado:** Pendiente de pago\n\n"
            "---\n\n"
            "### Deuda acumulada\n"
            "- **Total pendiente:** 240,00 €\n"
            "- **Facturas vencidas:** 2\n\n"
            "---\n\n"
            "### Múltiples facturas\n"
            "| Fecha de emisión | Estado    | Importe   |\n"
            "|:-----------------|:----------|----------:|\n"
            "| 2025-06-05       | Pendiente | 300,00 €  |\n"
            "| 2025-05-15       | Pagado    | 150,00 €  |\n\n"
            "**Total pendiente:** 300,00 €"
        )

    def can_handle(self, message: str) -> bool:
        # Solo maneja preguntas explícitas sobre facturas, pagos o deudas
        return bool(re.search(r"\b(factura|facturas|pago|pagos|deuda|importe|vencida|vencidas|recibo|recibos)\b", message, re.IGNORECASE))

    def handle_message(self, message: str) -> str:
        # Procesar el mensaje usando el ChatAgent y obtener la respuesta y el contexto
        response, tool_context = self.agent.handle_message_with_context(message)
        
        if tool_context:
            # Si hay respuesta de herramienta, formatear con el prompt especializado
            prompt = (
                f"Eres un asistente especializado en facturación. "
                f"Responde exclusivamente a preguntas sobre facturas, pagos y deudas. "
                f"Genera respuestas claras, concisas y bien estructuradas usando Markdown. "
                f"Solo muestra los datos que aparecen en la siguiente respuesta JSON, sin inventar ni añadir nada extra.\n\n"
                f"Respuesta de la herramienta:\n{tool_context}\n\n"
                f"Usuario: {message}"
            )
            final_response, _ = self.agent.handle_message_with_context(prompt)
            return final_response
        else:
            # Si no hay respuesta de herramienta, usar el prompt general
            mensaje_formateado = f"{self.prompt}\nUsuario: {message}"
            final_response, _ = self.agent.handle_message_with_context(mensaje_formateado)
            return final_response
