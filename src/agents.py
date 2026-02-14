import yaml
from crewai import Agent, LLM, Task
import config

def load_agents() -> list[Agent]:
    """
    Load agent configurations from YAML files and create agent instances
    """
    return [
        create_agent('agents/pm.yml', config.REASONING_LLM),
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
        llm=llm
    )

def load_main_task(project_description: str) -> Task:
    return create_task('agents/manager.yml', project_description)

def create_task(file_name: str, project_description: str) -> Task:
    """
    Load task configuration from a YAML file and create a task instance
    """
    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
    return Task(
        description=data['description'].format(project_description=project_description),
        expected_output=data['expected output']
    )
