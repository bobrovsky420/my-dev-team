import yaml
from crewai import Agent, LLM
from . import config

def load_agents() -> dict[Agent]:
    """
    Load agent configurations from YAML files and create agent instances
    """
    return {
        'pm': create_agent('agents/pm.yml', config.REASONING_LLM),
        'developer': create_agent('agents/developer.yml', config.DEV_LLM),
        'reviewer': create_agent('agents/reviewer.yml', config.QA_LLM)
    }

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
        llm=llm
    )
