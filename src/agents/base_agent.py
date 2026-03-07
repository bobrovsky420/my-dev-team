from abc import ABC
from functools import cached_property
import logging
import re
import yaml
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from utils import sanitize_for_prompt

def get_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Returns a configured LLM instance."""
    if model_name.startswith('ollama/'):
        return ChatOllama(model=model_name[7:], temperature=temperature)
    elif model_name.startswith('groq/'):
        if model_name == 'groq/compound':
            return ChatGroq(model=model_name, temperature=temperature, max_retries=2)
        return ChatGroq(model=model_name[5:], temperature=temperature, max_retries=2)
    raise ValueError(f"Unsupported model: {model_name}")

class BaseAgent(ABC):
    model_name: str = 'ollama/qwen3:8b'
    temperature: float = 0.2

    def __init__(self, config: dict, prompt_template: str, model: dict = None):
        self.config = config
        self.role = config.get('role', 'Agent')
        self.name = config.get('name', None)
        self.model_name = model.get('name') if model else config.get('model', self.model_name)
        self.temperature = model.get('temperature') if model else config.get('temperature', self.temperature)
        self.prompt_template = prompt_template
        self.logger = logging.getLogger(self.name or self.role)

    @cached_property
    def _required_inputs(self) -> list[str]:
        return self.config.get('required_inputs', [])

    @cached_property
    def _extract_patterns(self) -> dict[str, str]:
        return self.config.get('extract_patterns', {})

    @cached_property
    def _list_outputs(self) -> list[str]:
        return self.config.get('list_outputs', [])

    def _build_inputs(self, state: dict) -> dict:
        inputs = {}
        for key in self._required_inputs:
            val = state.get(key, '')
            inputs[key] = sanitize_for_prompt(str(val), [key]) if val else ''
        return inputs

    def _parse_outputs(self, response: str) -> dict:
        patterns = self._extract_patterns
        if not patterns:
            return {'raw_output': response}
        updates = {}
        for key, pattern in patterns.items():
            if matches := re.findall(pattern, response, re.DOTALL | re.IGNORECASE):
                clean_matches = []
                for m in matches:
                    if isinstance(m, tuple):
                        clean_tuple = tuple(item.strip() for item in m)
                        clean_matches.append(clean_tuple)
                    else:
                        if m.strip():
                            clean_matches.append(m.strip())
                if clean_matches:
                    updates[key] = clean_matches if key in self._list_outputs else clean_matches[0]
        return updates

    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        return parsed_data

    def process(self, state: dict) -> dict:
        self.logger.info("Executing...")
        inputs = self._build_inputs(state)
        response = self._invoke_llm(**inputs)
        parsed_data = self._parse_outputs(response)
        final_state = self._update_state(parsed_data, state)
        if 'communication_log' not in final_state:
            final_state['communication_log'] = [f"**[{self.name or self.role}]**: Completed step with response:\n```\n{response}\n```"]
        return final_state

    @cached_property
    def llm(self) -> BaseChatModel:
        return get_llm(model_name=self.model_name, temperature=self.temperature)

    @cached_property
    def prompt(self):
        return PromptTemplate.from_template(self.prompt_template)

    def _clean_response(self, text: str) -> str:
        """Removes DeepSeek <think> tags and returns the clean output."""
        cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        return cleaned_text.strip()

    def _invoke_llm(self, **kwargs) -> str:
        chain = self.prompt | self.llm
        response = self._clean_response(chain.invoke(kwargs).content)
        self.logger.debug("*"*50 + "\n%s\n" + "*"*50, response)
        return response

    @classmethod
    def from_config(cls, config_path: str):
        with open(config_path, 'r') as f:
            content = f.read()
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid format in {config_path}. Missing YAML frontmatter.")
        config = yaml.safe_load(parts[1])
        prompt = parts[2].strip()
        if 'models' in config:
            agents = []
            for model in config['models']:
                agent = cls(config, prompt, model)
                agents.append(agent)
            return agents
        else:
            return cls(config, prompt)
