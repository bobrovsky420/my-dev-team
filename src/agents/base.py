from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel

class BaseAgent(ABC):
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    @abstractmethod
    def process(self, state: dict) -> dict:
        """Processes the state and returns the updated state dictionary."""
        pass
