import yaml
from crewai import Agent, LLM
from crewai.tools import tool
from mail import mailpit as mail
from . import config

@tool
def ask_for_clarification(question: str, agent_role = 'Agent') -> str:
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
        'Crew Manager': create_agent('agents/manager.yml'),
        'Product Manager': create_agent('agents/pm.yml', tools=[ask_for_clarification]),
        'Developer': create_agent('agents/developer.yml'),
        'Code Reviewer': create_agent('agents/reviewer.yml')
    }

def create_agent(file_name: str, tools = None) -> Agent:
    """
    Load agent configuration from a YAML file and create an agent instance
    """
    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
    agent_config = {
        'role': data['role'],
        'goal': data['goal'],
        'backstory': data['backstory'],
        'llm': LLM(model=data['model'], base_url=config.BASE_URL, config={**config.DEFAULT_CONFIG, **data.get('config', {})}),
    }
    if data.get('allow delegation', False):
        agent_config['allow_delegation'] = True
    if 'max iterations' in data:
        agent_config['max_iter'] = data['max iterations']
    if tools:
        agent_config['tools'] = tools
    return Agent(**agent_config)
