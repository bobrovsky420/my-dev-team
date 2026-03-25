import asyncio
from functools import cached_property
from typing import Any, Generic, TypeVar
import traceback
import yaml
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel
from devteam.settings import get_config_dir, get_llm_timeout
from devteam.utils import LLMFactory, RateLimiter, WithLogging
from devteam.utils.sanitizer import sanitize_for_prompt

T = TypeVar('T', bound=BaseModel)

class BaseAgent(WithLogging, Generic[T]):
    """Base agent that uses LLM tool calling to submit structured results."""

    model_category: str = 'reasoning'
    temperature: float = 0.2
    max_retries: int = 2
    rate_limiter: RateLimiter = None
    output_schema: type[T]
    tools: list[type[BaseModel]]

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

    @staticmethod
    def sanitize_for_prompt(content: str, tags: list[str]) -> str:
        return sanitize_for_prompt(content, tags)

    @cached_property
    def inputs(self) -> list[str]:
        return self.config.get('inputs', [])

    @cached_property
    def outputs(self) -> list[str]:
        return self.config.get('outputs', [])

    def _build_inputs(self, state: dict) -> dict:
        inputs = {}
        for key in self.inputs:
            val = state.get(key, '')
            if key == 'messages': # Do not sanitize messages
                inputs[key] = val
            else:
                inputs[key] = self.sanitize_for_prompt(str(val), [key]) if val else ''
        return inputs

    def _update_state(self, parsed_data: T, current_state: dict) -> dict:
        return parsed_data.model_dump()

    async def process(self, state: dict) -> dict:
        self.logger.info("Executing...")
        inputs = self._build_inputs(state)
        try:
            self.logger.debug("Invoking LLM with inputs:\n%s", inputs)
            ai_message = await self._invoke_llm(**inputs)
            parsed_data = self._parse_outputs(ai_message)
        except Exception:  # pylint: disable=broad-exception-caught
            full_traceback = traceback.format_exc()
            return {
                'error': True,
                'error_message': full_traceback,
            }
        final_state = self._update_state(parsed_data, state)
        if 'messages' in self.outputs:
            final_state['messages'] = [ai_message]
        final_state['communication_log'] = [f"**[{self.name or self.role}]**: {ai_message.content}"]
        return final_state

    @cached_property
    def llm(self) -> Any:
        llm = self.llm_factory.create(
            category=self.model_category,
            temperature=self.temperature,
            node_name=self.node_name,
            json_mode=False
        )
        if self.tools:
            llm = llm.bind_tools(self.tools)
        return llm

    def _build_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ('system', self.prompt_template),
            MessagesPlaceholder(variable_name='messages', optional=True)
        ])

    @cached_property
    def chain(self) -> Any:
        return self._build_prompt() | self.llm

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
