import os
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

def new_llm(model_name: str, config_override: dict = None) -> LLM:
    """
    Create a new LLM instance with the given model name and default configuration
    """
    if model_name.startswith('ollama/'):
        return LLM(
            model=model_name,
            base_url=config.OLLAMA_URL,
            config={**config.OLLAMA_CONFIG, **(config_override or {})}
        )
    elif model_name.startswith('groq/'):
        return LLM(
            model=model_name,
            api_key=os.environ.get('GROQ_API_KEY'),
            temperature=config_override.get('temperature', config.GROQ_CONFIG.get('temperature', 0.7)),
            extra_body={
                'reasoning_format': 'hidden',
                'reasoning_effort': 'none'
            }
        )
    raise ValueError(f"Unsupported model: {model_name}")

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
        'llm': new_llm(data['model'], data.get('config')),
        'max_rpm': 2
    }
    if data.get('allow delegation', False):
        agent_config['allow_delegation'] = True
    if 'max iterations' in data:
        agent_config['max_iter'] = data['max iterations']
    if tools:
        agent_config['tools'] = tools
    return Agent(**agent_config)
