from functools import cached_property
import yaml
from langchain_core.language_models.chat_models import BaseChatModel
from devteam import settings

class LLMFactory:
    def __init__(self, provider: str, callbacks: list = None):
        self.provider = provider.lower()
        self.callbacks = callbacks or []
        if self.provider not in self.model_map:
            raise ValueError(f"Unsupported provider: {self.provider}")

    @cached_property
    def llm_config(self) -> dict:
        config_path = settings.config_dir / 'llms.yaml'
        return yaml.safe_load(config_path.read_text(encoding='utf-8'))

    @cached_property
    def model_map(self) -> dict:
        return self.llm_config.get('providers', {})

    def create(self, category: str, temperature: float, *, node_name: str, json_mode = True) -> BaseChatModel:
        """Returns a configured LLM instance."""
        # pylint: disable=import-error,import-outside-toplevel
        model_name = self.model_map[self.provider].get(category, self.model_map[self.provider]['reasoning'])
        streaming = settings.llm_streaming
        node_tag = f'node:{node_name}'
        llm_tags = [node_tag]
        match self.provider:
            case 'ollama':
                from langchain_ollama import ChatOllama
                return ChatOllama(
                    model=model_name,
                    temperature=temperature,
                    streaming=streaming,
                    callbacks=self.callbacks,
                    tags=llm_tags,
                    format='json' if json_mode else None,
                    reasoning=streaming and not json_mode # Stream reasoning if enabled via CLI and not in strict JSON mode
                )
            case 'groq':
                from langchain_groq import ChatGroq
                llm = ChatGroq(
                    model=model_name,
                    temperature=temperature,
                    streaming=settings.llm_streaming,
                    callbacks=self.callbacks,
                    tags=llm_tags,
                    max_retries=2
                )
                if json_mode:
                    return llm.bind(response_format={'type': 'json_object'})
                return llm
            case 'openai':
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    streaming=settings.llm_streaming,
                    callbacks=self.callbacks,
                    tags=llm_tags
                )
            case _:
                raise ValueError(f"Unsupported provider: {self.provider}")
