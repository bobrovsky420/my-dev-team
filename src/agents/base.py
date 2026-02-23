from abc import ABC, abstractmethod
from functools import cached_property
import yaml
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

def get_llm(model_name: str, temperature: float):
    """Returns a configured LLM instance."""
    if model_name.startswith('ollama/'):
        return ChatOllama(model=model_name[7:], temperature=temperature)
    raise ValueError(f"Unsupported model: {model_name}")

class BaseAgent(ABC):
    model_name: str = 'ollama/qwen3:8b'
    temperature: float = 0.2
    prompt_template: str

    @abstractmethod
    def process(self, state: dict) -> dict:
        """Processes the state and returns the updated state dictionary."""
        pass

    @cached_property
    def prompt(self):
        return PromptTemplate.from_template(self.prompt_template)

    @classmethod
    def from_config(cls, config_path: str):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        agent = cls()
        agent.model_name = config.get('model', agent.model_name)
        agent.temperature = config.get('temperature', agent.temperature)
        agent.prompt_template = config.get('prompt')
        agent.llm = get_llm(model_name=agent.model_name, temperature=agent.temperature)
        return agent
