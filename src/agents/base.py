from abc import ABC, abstractmethod
from .config import get_llm

class BaseAgent(ABC):
    model_name = 'qwen3:8b'

    def __init__(self):
        self.llm = get_llm(model_name=self.model_name)

    @abstractmethod
    def process(self, state: dict) -> dict:
        """Processes the state and returns the updated state dictionary."""
        pass
