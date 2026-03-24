import asyncio
from functools import cached_property
from typing import Any, Generic, TypeVar
import logging
import traceback
import yaml
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, ValidationError
from devteam.settings import get_config_dir, get_llm_timeout
from devteam.utils import LLMFactory, RateLimiter
from devteam.utils.sanitizer import sanitize_for_prompt

T = TypeVar('T', bound=BaseModel)

class BaseAgent(Generic[T]):
    """Base agent that uses LLM tool calling to submit structured results."""

    model_category: str = 'reasoning'
    temperature: float = 0.2
    max_retries: int = 2
    rate_limiter: RateLimiter = None
    output_schema: type[T]
    tools: list[type[BaseModel]]

    chain: Any # type: ignore

    def __init__(self, config: dict, prompt_template: str, node_name: str, llm_factory: LLMFactory = None, rate_limiter: RateLimiter = None):
        self.config = config
        self.prompt_template = prompt_template
        self.node_name = node_name
        self.llm_factory = llm_factory
        self.rate_limiter = rate_limiter
        self.role = config.get('role', 'Agent')
        self.name = config.get('name', None)
        self.model_category = config.get('model', self.model_category)
        self.temperature = config.get('temperature', self.temperature)
        self.logger = logging.getLogger(self.name or self.role)

    @staticmethod
    def sanitize_for_prompt(content: str, tags: list[str]) -> str:
        return sanitize_for_prompt(content, tags)

    @cached_property
    def required_inputs(self) -> list[str]:
        return self.config.get('required_inputs', [])

    def _build_inputs(self, state: dict) -> dict:
        inputs = {}
        for key in self.required_inputs:
            val = state.get(key, '')
            inputs[key] = self.sanitize_for_prompt(str(val), [key]) if val else ''
        return inputs

    def _update_state(self, parsed_data: T, current_state: dict) -> dict:
        return parsed_data.model_dump()

    async def process(self, state: dict) -> dict:
        self.logger.info("Executing...")
        inputs = self._build_inputs(state)
        self._build_chain(self.temperature)
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                ai_message = await self._invoke_llm(**inputs)
                parsed_data = self._parse_outputs(ai_message)
            except (ValueError, ValidationError) as e:
                last_error = e
                self.logger.error(
                    "Attempt %i/%i failed to parse: %s",
                    attempt, self.max_retries, e,
                )
                if attempt < self.max_retries:
                    self._bump_temperature(attempt, last_error)
                continue
            except Exception:  # pylint: disable=broad-exception-caught
                full_traceback = traceback.format_exc()
                return {
                    'error': True,
                    'error_message': full_traceback,
                }
            final_state = self._update_state(parsed_data, state)
            content = ai_message.content or ''
            if 'communication_log' not in final_state:
                final_state['communication_log'] = [
                    f"**[{self.name or self.role}]**: {content}"
                ]
            return final_state

        self.logger.error(
            "All %i attempts failed. Last error: %s",
            self.max_retries, last_error,
        )
        return {
            'abort_requested': True,
            'communication_log': [
                f"**[{self.name or self.role}]**: Failed after "
                f"{self.max_retries} attempts. Last error: {last_error}"
            ],
        }

    def _bump_temperature(self, attempt: int, last_error: Exception):
        new_temp = min(self.temperature + (attempt * 0.1), 1.0)
        self.logger.debug("Bumping temperature to %.1f for retry", new_temp)
        retry_prompt = self._bump_prompt(last_error)
        self._build_chain(temperature=new_temp, retry_prompt=retry_prompt)

    def _bump_prompt(self, last_error: Exception) -> str:
        if isinstance(last_error, ValidationError):
            error_details = [
                f"Field '{e.get('loc', [''])[0]}': {e.get('msg', '')}"
                for e in last_error.errors()
            ]
            concise_error = "Schema mismatch: " + "; ".join(error_details)
        else:
            concise_error = str(last_error).split('\n', maxsplit=1)[0][:200]
        error_msg = concise_error.replace('{', '{{').replace('}', '}}')
        return (
            f"### ERROR ON PREVIOUS ATTEMPT ###\n"
            f"{error_msg}\n\n"
            f"You MUST call one of the provided tools to submit your work. "
            f"Do NOT respond with plain text only — use a tool call."
        )

    def _build_chain(self, temperature: float, retry_prompt: str = None):
        llm = self.llm_factory.create(
            category=self.model_category,
            temperature=temperature,
            node_name=self.node_name,
            json_mode=False,
        )
        llm_with_tools = llm.bind_tools(self.tools)
        prompt = self._build_prompt(retry_prompt)
        self.chain = prompt | llm_with_tools

    def _build_prompt(self, retry_prompt: str = None) -> PromptTemplate:
        template = self.prompt_template
        if retry_prompt:
            template += f"\n\n{retry_prompt}"
        return PromptTemplate(template=template)

    @cached_property
    def llm_timeout(self) -> int:
        return get_llm_timeout()

    async def _invoke_llm(self, **kwargs) -> Any:
        if self.rate_limiter:
            await self.rate_limiter.wait_if_needed()
        try:
            response = await asyncio.wait_for(
                self.chain.ainvoke(kwargs), timeout=self.llm_timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"LLM call timed out after {self.llm_timeout} seconds"
            ) from None
        self.logger.debug("Raw Response Content:\n%s", response.content)
        self.logger.debug("Tool Calls:\n%s", response.tool_calls)
        return response

    def _parse_outputs(self, response) -> T:
        if not response.tool_calls:
            raise ValueError(
                "The model did not call any tool. "
                "You MUST call one of the provided tools to submit your work."
            )
        tool_call = response.tool_calls[0]
        return self._map_tool_to_output(tool_call['name'], tool_call['args'])

    def _map_tool_to_output(self, tool_name: str, tool_args: dict) -> T:
        """Map a tool call to the agent's output schema."""
        return self.output_schema(**tool_args)

    @classmethod
    def from_config(cls, node_name: str, config_path: str, *, llm_factory: LLMFactory = None, rate_limiter: RateLimiter = None, model_category: str = None, temperature: float = None):
        prompt_file = get_config_dir() / 'agents' / config_path
        try:
            content = prompt_file.read_text(encoding='utf-8')
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find agent prompt '{config_path}' in {prompt_file.parent}") from e
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid format in {config_path}. Missing YAML frontmatter")
        config = yaml.safe_load(parts[1])
        prompt = parts[2].strip()
        if model_category is not None:
            config['model'] = model_category
        if temperature is not None:
            config['temperature'] = temperature
        return cls(config, prompt, node_name, llm_factory=llm_factory, rate_limiter=rate_limiter)
