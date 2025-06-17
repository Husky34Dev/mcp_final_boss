# app/agent/default_agent.py

import re

class DefaultAgent:
    def __init__(self, chat_agent):
        self.agent = chat_agent
        self.prompt = (
            "Eres un asistente general. "
            "Responde de forma clara, profesional y útil a cualquier consulta que no sea de facturación o incidencias técnicas. "
            "Si el usuario pide los datos de un abonado, muestra únicamente los datos reales que devuelve la herramienta de datos de abonado: nombre, dni, dirección, correo, teléfono y póliza. "
            "No inventes ni añadas información como deuda, estado de pagos o facturas si no se solicita explícitamente y no está en la respuesta de la herramienta. "
            "Formatea la respuesta en Markdown profesional y claro. Usa títulos y listas si es útil. "
            "Ejemplo de formato para datos de abonado:\n\n"
            "### Datos del abonado\n"
            "- **Nombre:** Ana López\n"
            "- **DNI:** 12345678A\n"
            "- **Dirección:** Calle de la Constitución, 12, 28012 Madrid\n"
            "- **Correo electrónico:** ana@example.com\n"
            "- **Teléfono:** 987654321\n"
            "- **Póliza:** POL123\n\n"
            "Si necesitas mostrar varios elementos, usa listas o tablas Markdown."
        )

    def can_handle(self, message: str) -> bool:
        # Solo maneja preguntas generales o de datos personales, no de facturación ni incidencias
        return not (re.search(r"\b(factura|facturas|pago|pagos|deuda|importe|vencida|vencidas|recibo|recibos)\b", message, re.IGNORECASE) or                    re.search(r"\b(incidencia|avería|averias|reporte|problema|zona|corte|caída|caida|fallo|fallos)\b", message, re.IGNORECASE))

    def handle_message(self, message: str) -> str:
        # El modelo ya tiene acceso al JSON de la herramienta en su contexto de chat
        mensaje_formateado = f"{self.prompt}\nUsuario: {message}"
        return self.agent.handle_message(mensaje_formateado)
