# app/agent/default_agent.py

class DefaultAgent:
    def __init__(self, chat_agent):
        self.agent = chat_agent

    def can_handle(self, message: str) -> bool:
        return True

    def handle_message(self, message: str) -> str:
        return self.agent.handle_message(message)
