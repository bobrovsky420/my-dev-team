from functools import cached_property
from importlib import resources
from typing import Generic, TypeVar
import json
import logging
import re
import yaml
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ValidationError
from ..utils import RateLimiter, sanitize_for_prompt
from .llm_config import get_llm

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
        if isinstance(last_error, ValidationError):
            error_details = [f"Field '{e.get('loc', [''])[0]}': {e.get('msg', '')}" for e in last_error.errors()]
            concise_error = "Schema mismatch: " + "; ".join(error_details)
        else:
            error_str = str(last_error)
            concise_error = error_str.split('\n')[0][:150]
            if "Invalid json output" in concise_error:
                concise_error = "Invalid JSON syntax. You likely included Markdown formatting or text outside the JSON brackets."
        error_msg = concise_error.replace('{', '{{').replace('}', '}}')
        self._retry_prompt = (
            f"### VALIDATION ERROR ON PREVIOUS ATTEMPT ###\n"
            f"Your previous response failed schema validation with the following error:\n"
            f"{error_msg}\n\n"
            f"Please analyze the error above and correct your output. "
            f"You must return ONLY raw, valid JSON that strictly conforms to the requested schema. "
            f"Do NOT wrap the output in markdown code blocks."
        )
        self.__dict__.pop('prompt', None)

    @cached_property
    def llm(self) -> BaseChatModel:
        return get_llm(model_name=self.model_name, temperature=getattr(self, '_retry_temperature', self.temperature))

    @cached_property
    def prompt(self):
        base_template = self.prompt_template + "\n\n# Output Format\n{format_instructions}"
        if hasattr(self, '_retry_prompt'):
            base_template += f"\n\n{self._retry_prompt}"
        return PromptTemplate(
            template=base_template,
            partial_variables={'format_instructions': self.parser.get_format_instructions()}
        )

    @cached_property
    def parser(self) -> PydanticOutputParser:
        return PydanticOutputParser(pydantic_object=self.output_schema)

    async def _invoke_llm(self, **kwargs) -> str:
        chain = self.prompt | self.llm
        if self.rate_limiter:
            await self.rate_limiter.wait_if_needed()
        response = await chain.ainvoke(kwargs)
        response = response.content
        self.logger.debug("*"*50 + "\n%s\n" + "*"*50, response)
        return response

    def _clean_response(self, text: str) -> str:
        """Removes DeepSeek <think> tags and returns the clean output."""
        cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        return cleaned_text.strip()

    def _parse_outputs(self, response: str) -> T:
        try:
            clean_json = self._clean_response(response)
            clean_json = clean_json.replace('```json', '').replace('```', '').strip()
            return self.parser.invoke(clean_json)
        except ValidationError as e:
            raise ValidationError(f"Schema mismatch: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse JSON. Error: {e}")

    @classmethod
    def from_config(cls, config_path: str):
        package_path = 'my_dev_team.agents.prompts'
        try:
            prompt_file = resources.files(package_path).joinpath(config_path)
            content = prompt_file.read_text(encoding='utf-8')
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find '{config_path}' in the package '{package_path}'")
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid format in {config_path}. Missing YAML frontmatter")
        config = yaml.safe_load(parts[1])
        prompt = parts[2].strip()
        if 'models' in config:
            agents = []
            for model in config['models']:
                agent = cls(config, prompt, model)
                agents.append(agent)
            return agents
        return cls(config, prompt)
