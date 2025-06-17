# app/agent/incidencia_agent.py
import re

class IncidenciaAgent:
    def __init__(self, chat_agent):
        self.agent = chat_agent

    def can_handle(self, message: str) -> bool:
        return bool(re.search(r"incidencia|avería|zona|reporte", message, re.IGNORECASE))

    def handle_message(self, message: str) -> str:
        return self.agent.handle_message(message)
