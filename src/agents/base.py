from abc import ABC, abstractmethod
from functools import cached_property
import logging
import re
import yaml
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

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

    def __init__(self, role: str):
        self.role = role
        self.logger = logging.getLogger(self.role)

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

    def clean_response(self, text: str) -> str:
        """Removes DeepSeek <think> tags and returns the clean output."""
        cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        return cleaned_text.strip()

    def invoke_llm(self, args) -> str:
        chain = self.prompt | self.llm
        response = self.clean_response(chain.invoke(args).content)
        self.logger.debug("*"*50 + "\n%s\n" + "*"*50, response)
        return response

    @classmethod
    def from_config(cls, config_path: str):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        agent = cls(config['role'])
        agent.model_name = config.get('model', agent.model_name)
        agent.temperature = config.get('temperature', agent.temperature)
        agent.prompt_template = config['prompt']
        return agent
