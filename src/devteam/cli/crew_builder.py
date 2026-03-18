from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from devteam import LLMFactory, ProjectManager, VirtualCrew
from devteam.extensions import ConsoleLogger, HumanInTheLoop, WorkspaceSaver
from devteam.utils import RateLimiter, build_agents_from_config

BASIC_CREW = 'basic.yaml'

def my_extensions(project_folder) -> list:
    return [
        ConsoleLogger(),
        WorkspaceSaver(workspace_dir=project_folder),
        HumanInTheLoop(),
    ]

def build_crew(llm_factory: LLMFactory, checkpointer: AsyncSqliteSaver, rpm: int = 0, extensions: list = None, config_name: str = None) -> VirtualCrew:
    """Instantiates the agents and returns the crew instance."""
    return VirtualCrew(
        manager=ProjectManager(),
        agents=build_agents_from_config(config_name or BASIC_CREW),
        extensions=extensions or [],
        llm_factory=llm_factory,
        checkpointer=checkpointer,
        rate_limiter=RateLimiter(requests_per_minute=rpm) if rpm > 0 else None,
    )
