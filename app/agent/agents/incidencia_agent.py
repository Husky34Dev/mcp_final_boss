# app/agent/incidencia_agent.py
import re

class IncidenciaAgent:
    def __init__(self, chat_agent):
        self.agent = chat_agent
        self.prompt = (
            "Eres un asistente experto en incidencias técnicas. "
            "Responde solo sobre incidencias, averías o reportes técnicos. "
            "Formatea la respuesta en Markdown profesional y claro. Usa títulos, listas o tablas según el tipo de consulta. "
            "Adapta el formato según la consulta del usuario.\n\n"
            "Ejemplos de formato:\n\n"
            "### Incidencia Reportada\n"
            "- **Ubicación:** Centro de la ciudad\n"
            "- **Descripción:** Corte de servicio por mantenimiento\n"
            "- **Estado:** En resolución\n\n"
            "### Lista de Incidencias\n"
            "| Ubicación | Descripción | Estado |\n"
            "|:----------|:------------|:-------|\n"
            "| Zona Norte | Caída de red | Resuelta |\n"
            "| Zona Sur | Baja velocidad | En proceso |\n\n"
            "---\n\n"
            "### Nueva Incidencia\n"
            "✅ **Incidencia creada exitosamente**\n"
            "- **ID:** INC-2025-001\n"
            "- **Ubicación:** Calle Principal\n"
            "- **Estado:** Abierta\n"
            "- **Seguimiento:** Se ha notificado al equipo técnico"
        )

    def can_handle(self, message: str) -> bool:
        # Solo maneja preguntas relacionadas con incidencias técnicas
        return bool(re.search(r"\b(incidencia|avería|averias|reporte|problema|zona|corte|caída|caida|fallo|fallos)\b", message, re.IGNORECASE))

    def handle_message(self, message: str) -> str:
        # Procesar el mensaje usando el ChatAgent y obtener la respuesta y el contexto
        response, tool_context = self.agent.handle_message_with_context(message)
        
        if tool_context:
            # Si hay respuesta de herramienta, formatear con el prompt especializado
            prompt = (
                f"Eres un asistente especializado en incidencias técnicas. "
                f"Genera respuestas claras y profesionales usando Markdown. "
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