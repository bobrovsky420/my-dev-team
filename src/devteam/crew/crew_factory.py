from pathlib import Path
from langgraph.checkpoint.memory import MemorySaver
from devteam.managers import ProjectManager
from devteam.utils import LLMFactory, RateLimiter
from .agents_factory import AgentsFactory
from .crew import VirtualCrew

class CrewFactory:
    BASIC_CREW = 'basic.yaml'

    def __init__(self, llm_factory: LLMFactory = None, agents_factory: AgentsFactory = None):
        self.llm_factory = llm_factory or self.default_llm_factory()
        self.agents_factory = agents_factory or AgentsFactory()

    @classmethod
    def default_agents_factory(cls):
        return AgentsFactory()

    @classmethod
    def default_llm_factory(cls):
        return LLMFactory(provider='ollama')

    def create(self, project_folder: Path, *, checkpointer = None, rpm: int = 0, extensions: list = None, config_name: str = None):
        return VirtualCrew(
            project_folder,
            manager=ProjectManager(),
            agents=self.agents_factory.create_agents(config_name or self.BASIC_CREW),
            llm_factory=self.llm_factory,
            checkpointer=checkpointer or MemorySaver(),
            extensions=extensions or [],
            rate_limiter=RateLimiter(requests_per_minute=rpm) if rpm > 0 else None,
        )
