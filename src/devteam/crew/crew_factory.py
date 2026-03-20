from pathlib import Path
from langgraph.checkpoint.memory import MemorySaver
from devteam.managers import ProjectManager
from devteam.utils import LLMFactory, RateLimiter, build_agents_from_config
from .crew import VirtualCrew

class CrewFactory:
    BASIC_CREW = 'basic.yaml'

    def __init__(self, llm_factory: LLMFactory = None):
        self.llm_factory = llm_factory or self.default_llm_factory()

    @staticmethod
    def default_llm_factory():
        return LLMFactory(provider='ollama')

    def create(self, project_folder: Path, *, checkpointer = None, rpm: int = 0, extensions: list = None, config_name: str = None):
        return VirtualCrew(
            project_folder,
            manager=ProjectManager(),
            agents=build_agents_from_config(config_name or self.BASIC_CREW),
            llm_factory=self.llm_factory,
            checkpointer=checkpointer or MemorySaver(),
            extensions=extensions or [],
            rate_limiter=RateLimiter(requests_per_minute=rpm) if rpm > 0 else None,
        )
