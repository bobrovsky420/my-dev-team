import yaml
from crewai import Agent, LLM
from crewai.tools import tool
from human import mailpit as mail
from . import config

@tool
def ask_for_clarification(question: str, agent_role: str = 'Agent') -> str:
    """
    Ask a clarifying question to the human stakeholder and wait for their response
    """
    mail.send_question(question, role=agent_role)
    response = mail.wait_for_clarification()
    return response or "No response received within timeout period"

def load_agents() -> dict[str, Agent]:
    """
    Load agent configurations from YAML files and create agent instances
    """
    return {
        'pm': create_agent('agents/pm.yml', config.PM_LLM, tools=[ask_for_clarification]),
        'developer': create_agent('agents/developer.yml', config.DEV_LLM),
        'reviewer': create_agent('agents/reviewer.yml', config.QA_LLM)
    }

def create_agent(file_name: str, llm: LLM, tools=None) -> Agent:
    """
    Load agent configuration from a YAML file and create an agent instance
    """
    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
    agent_config = {
        'role': data['role'],
        'goal': data['goal'],
        'backstory': data['backstory'],
        'llm': llm,
        'verbose': True
    }
    if data.get('allow delegation', False):
        agent_config['allow_delegation'] = True
    if tools:
        agent_config['tools'] = tools
    return Agent(**agent_config)
