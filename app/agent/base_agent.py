from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def can_handle(self, message: str) -> bool:
        """¿Puede este agente gestionar el mensaje?"""
        ...

    @abstractmethod
    def system_prompt(self) -> str:
        """Prompt del sistema específico de este agente"""
        ...