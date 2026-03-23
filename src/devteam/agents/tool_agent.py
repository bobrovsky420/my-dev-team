import asyncio
import traceback
from typing import Any, TypeVar
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, ValidationError
from .base_agent import BaseAgent

T = TypeVar('T', bound=BaseModel)

class ToolAgent(BaseAgent[T]):
    """Base agent that uses LLM tool calling instead of structured JSON output."""

    tools: list[type[BaseModel]]

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
        """Map a tool call to the agent's output schema. Override in subclasses."""
        raise NotImplementedError

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
            except Exception:
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
