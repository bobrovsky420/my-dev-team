from functools import cached_property
from typing import Generic, TypeVar
import json
import logging
import re
import yaml
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from pydantic import BaseModel, ValidationError
from utils import RateLimiter, sanitize_for_prompt

def get_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Returns a configured LLM instance."""
    if model_name.startswith('ollama/'):
        return ChatOllama(model=model_name[7:], temperature=temperature)
    elif model_name.startswith('groq/'):
        if model_name == 'groq/compound':
            return ChatGroq(model=model_name, temperature=temperature, max_retries=2)
        return ChatGroq(model=model_name[5:], temperature=temperature, max_retries=2)
    raise ValueError(f"Unsupported model: {model_name}")

T = TypeVar('T', bound=BaseModel)

class BaseAgent(Generic[T]):
    model_name: str = 'ollama/qwen3:8b'
    temperature: float = 0.2
    max_retries: int = 2
    rate_limiter: RateLimiter = None
    output_schema: type[T]

    def __init__(self, config: dict, prompt_template: str, model: dict = None):
        self.config = config
        self.role = config.get('role', 'Agent')
        self.name = config.get('name', None)
        self.model_name = model.get('name') if model else config.get('model', self.model_name)
        self.temperature = model.get('temperature') if model else config.get('temperature', self.temperature)
        self.prompt_template = prompt_template
        self.logger = logging.getLogger(self.name or self.role)

    @cached_property
    def required_inputs(self) -> list[str]:
        return self.config.get('required_inputs', [])

    def _build_inputs(self, state: dict) -> dict:
        inputs = {}
        for key in self.required_inputs:
            val = state.get(key, '')
            inputs[key] = sanitize_for_prompt(str(val), [key]) if val else ''
        return inputs

    def _parse_outputs(self, response: str) -> T:
        if fenced_match := re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL | re.IGNORECASE):
            payload = fenced_match.group(1)
        elif json_match := re.search(r'(\{.*\})', response, re.DOTALL):
            payload = json_match.group(1)
        else:
            raise ValueError("No JSON payload found in the response.")
        return self.output_schema.model_validate(json.loads(payload))

    def _update_state(self, parsed_data: T, current_state: dict) -> dict:
        return parsed_data.model_dump()

    def _reset_run_state(self):
        if hasattr(self, '_retry_temperature'):
            del self._retry_temperature
            self.__dict__.pop('llm', None)
        if hasattr(self, '_retry_prompt'):
            del self._retry_prompt
            self.__dict__.pop('prompt', None)

    async def process(self, state: dict) -> dict:
        self.logger.info("Executing...")
        self._reset_run_state()
        inputs = self._build_inputs(state)
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            response = await self._invoke_llm(**inputs)
            try:
                parsed_data = self._parse_outputs(response)
            except (ValueError, ValidationError, json.JSONDecodeError) as e:
                last_error = e
                self.logger.error("Attempt %i/%i failed to parse: %s", attempt, self.max_retries, e)
                if attempt < self.max_retries:
                    self._bump_temperature(attempt)
                    self._bump_prompt(last_error)
                continue
            final_state = self._update_state(parsed_data, state)
            if 'communication_log' not in final_state:
                final_state['communication_log'] = [f"**[{self.name or self.role}]**: Completed step with response:\n```\n{response}\n```"]
            return final_state
        self.logger.error("All %i attempts failed. Last error: %s", self.max_retries, last_error)
        return {
            'abort_requested': True,
            'communication_log': [f"**[{self.name or self.role}]**: Failed after {self.max_retries} attempts. Last error: {last_error}"]
        }

    def _bump_temperature(self, attempt: int):
        new_temp = min(self.temperature + (attempt * 0.1), 1.0)
        self.logger.info("Bumping temperature to %.1f for retry", new_temp)
        self._retry_temperature = new_temp
        self.__dict__.pop('llm', None)

    def _bump_prompt(self, last_error: Exception):
        self._retry_prompt = self.prompt_template + "\n\n" + (
            f"YOUR PREVIOUS RESPONSE COULD NOT BE PARSED. Error: {last_error}\n"
            f"You MUST respond with valid JSON matching the required schemd. "
            f"Wrap your JSON in ```json ... ``` fences. "
            f"Do not include any text inside the JSON block that is not valid JSON."
        )
        self.__dict__.pop('prompt', None)

    @cached_property
    def llm(self) -> BaseChatModel:
        return get_llm(model_name=self.model_name, temperature=getattr(self, '_retry_temperature', self.temperature))

    @cached_property
    def prompt(self):
        return PromptTemplate.from_template(getattr(self, '_retry_prompt', self.prompt_template))

    def _clean_response(self, text: str) -> str:
        """Removes DeepSeek <think> tags and returns the clean output."""
        cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        return cleaned_text.strip()

    async def _invoke_llm(self, **kwargs) -> str:
        chain = self.prompt | self.llm
        if self.rate_limiter:
            await self.rate_limiter.wait_if_needed()
        response = await chain.ainvoke(kwargs)
        response = self._clean_response(response.content)
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
