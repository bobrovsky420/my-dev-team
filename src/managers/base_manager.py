from abc import ABC, abstractmethod
import logging
from langgraph.graph import StateGraph

class BaseManager(ABC):
    role = 'Crew Manager'
    name: str = None

    def __init__(self):
        self.logger = logging.getLogger(self.name or self.role)

    @abstractmethod
    def build_graph(self, agents: dict, developers: dict, memory, human_interrupter) -> StateGraph:
        """Constructs and compiles the specific LangGraph workflow for this manager"""
        pass
