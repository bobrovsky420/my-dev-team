from functools import cached_property
import logging
from pydantic import BaseModel
from devteam import settings
from devteam.state import ProjectState
from devteam.tools.registry import tool_registry
from . import schemas


class IntermediateTools:
    """Mixin that resolves tool schemas from the registry and dispatches intermediate tool calls."""

    config: dict
    logger: logging.Logger

    @cached_property
    def tools(self) -> list[type[BaseModel]]:
        tools = []
        for name in self.config.get('tools', []):
            if entry := tool_registry.get(name):
                if entry.is_enabled(settings):
                    tools.append(entry.schema)
                continue
            if schema := getattr(schemas, name, None):
                tools.append(schema)
            else:
                self.logger.warning("Unknown tool '%s' in config, skipping.", name)
        return tools

    async def _handle_intermediate_tools(self, tool_name: str, tool_args: dict, state: ProjectState) -> str:
        entry = tool_registry.get(tool_name)
        if entry is None:
            return None
        if not entry.is_enabled(settings):
            if entry.disabled_message:
                self.logger.warning("Agent attempted to call disabled tool '%s'. Instructing agent to proceed without it.", tool_name)
                return entry.disabled_message
            return None
        if entry.handler is None:
            return None
        return await entry.handler(tool_args, state, self.logger)
