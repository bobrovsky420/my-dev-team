from functools import cached_property
import yaml
from langchain_core.language_models.chat_models import BaseChatModel
from ..settings import get_config_dir

class LLMFactory:
    def __init__(self, provider: str, callbacks: list = None):
        self.provider = provider.lower()
        self.callbacks = callbacks or []
        if self.provider not in self.model_map:
            raise ValueError(f"Unsupported provider: {self.provider}")

    @cached_property
    def llm_config(self) -> dict:
        config_path = get_config_dir() / 'llms.yaml'
        return yaml.safe_load(config_path.read_text(encoding='utf-8'))

    @cached_property
    def model_map(self) -> dict:
        return self.llm_config.get('providers', {})

    def create(self, category: str, temperature: float, *, node_name: str = None) -> BaseChatModel:
        """Returns a configured LLM instance."""
        # pylint: disable=import-error,import-outside-toplevel
        model_name = self.model_map[self.provider].get(category, self.model_map[self.provider]['reasoning'])
        match self.provider:
            case 'ollama':
                from langchain_ollama import ChatOllama
                return ChatOllama(
                    model=model_name,
                    temperature=temperature,
                    callbacks=self.callbacks,
                    tags=[f'node:{node_name}'],
                    format='json'
                )
            case 'groq':
                from langchain_groq import ChatGroq
                llm = ChatGroq(
                    model=model_name,
                    temperature=temperature,
                    callbacks=self.callbacks,
                    tags=[f'node:{node_name}'],
                    max_retries=2
                )
                return llm.bind(response_format={'type': 'json_object'})
            case 'openai':
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    callbacks=self.callbacks,
                    tags=[f'node:{node_name}']
                )
            case _:
                raise ValueError(f"Unsupported provider: {self.provider}")
