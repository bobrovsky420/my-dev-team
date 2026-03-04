from abc import ABC, abstractmethod
import logging

class BaseManager(ABC):
    role = 'Crew Manager'
    name: str = None

    def __init__(self):
        self.logger = logging.getLogger(self.name or self.role)

    @abstractmethod
    def router(self, state: dict) -> str:
        """Determines the next node in the LangGraph workflow"""
        pass

    @abstractmethod
    def queue_manager(self, state: dict) -> dict:
        """Pops the next task and resets task-specific environment variables"""
        pass
