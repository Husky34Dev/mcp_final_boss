# app/agent/factura_agent.py
import re

class FacturaAgent:
    def __init__(self, chat_agent):
        self.agent = chat_agent

    def can_handle(self, message: str) -> bool:
        return bool(re.search(r"factura|pago|deuda", message, re.IGNORECASE))

    def handle_message(self, message: str) -> str:
        return self.agent.handle_message(message)
