from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def can_handle(self, message: str) -> bool:
        pass

    @abstractmethod
    def handle(self, message: str, context: dict) -> str:
        pass
