import yaml
from crewai import Agent, LLM
from . import config

def load_agents() -> list[Agent]:
    """
    Load agent configurations from YAML files and create agent instances
    """
    return [
        create_agent('agents/pm.yml', config.PM_LLM),
        create_agent('agents/developer.yml', config.DEV_LLM),
        create_agent('agents/reviewer.yml', config.QA_LLM)
    ]

def create_agent(file_name: str, llm: LLM) -> Agent:
    """
    Load agent configuration from a YAML file and create an agent instance
    """
    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
    return Agent(
        role=data['role'],
        goal=data['goal'],
        backstory=data['backstory'],
        allow_delegation=data.get('allow delegation', False),
        llm=llm,
        verbose=True
    )
