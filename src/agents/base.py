from abc import ABC, abstractmethod
from functools import cached_property
import logging
import os
import re
from pathlib import Path
import yaml
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from .skills import load_skill_as_agent

class AgentYamlLoader(yaml.SafeLoader):
    pass

    @staticmethod
    def yaml_include(loader: yaml.Loader, node: yaml.Node):
        file_name, include_node = node.value.split('/', 1)
        file_path = os.path.join(os.path.dirname(loader.name), file_name)
        with open(file_path, 'r', encoding='utf-8') as input_file:
            include_file = yaml.load(input_file, Loader=yaml.SafeLoader)
        return include_file[include_node]

AgentYamlLoader.add_constructor('!include', AgentYamlLoader.yaml_include)

def get_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Returns a configured LLM instance."""
    if model_name.startswith('ollama/'):
        return ChatOllama(model=model_name[7:], temperature=temperature)
    elif model_name.startswith('groq/'):
        return ChatGroq(model=model_name[5:], temperature=temperature)
    raise ValueError(f"Unsupported model: {model_name}")

class BaseAgent(ABC):
    model_name: str = 'ollama/qwen3:8b'
    temperature: float = 0.2
    prompt_template: str
    llm: BaseChatModel

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(self.name)

    @abstractmethod
    def process(self, state: dict) -> dict:
        """Processes the state and returns the updated state dictionary."""
        pass

    @cached_property
    def llm(self):
        return get_llm(model_name=self.model_name, temperature=self.temperature)

    @cached_property
    def prompt(self):
        return PromptTemplate.from_template(self.prompt_template)

    def _clean_response(self, text: str) -> str:
        """Removes DeepSeek <think> tags and returns the clean output."""
        cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        return cleaned_text.strip()

    def invoke_llm(self, **kwargs) -> str:
        chain = self.prompt | self.llm
        response = self._clean_response(chain.invoke(kwargs).content)
        self.logger.debug("*"*50 + "\n%s\n" + "*"*50, response)
        return response

    @classmethod
    def from_config(cls, config_path: str):
        config = load_skill_as_agent(Path(config_path))
        if 'models' in config:
            agents = []
            for model in config['models']:
                agent = cls(config['name'])
                agent.model_name = model.get('name', agent.model_name)
                agent.temperature = model.get('temperature', agent.temperature)
                agent.prompt_template = config['prompt']
                agents.append(agent)
            return agents
        else:
            agent = cls(config['name'])
            agent.model_name = config.get('model', agent.model_name)
            agent.temperature = config.get('temperature', agent.temperature)
            agent.prompt_template = config['prompt']
            return agent
