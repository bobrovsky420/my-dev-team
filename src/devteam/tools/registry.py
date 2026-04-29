import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pydantic import BaseModel
from devteam.agents.schemas import AskClarification
from devteam.skills import skills
from devteam.state import ProjectState
from devteam.tools import rag
from devteam.tools.schemas import LoadSkill, ReadFile, ListFiles, GlobFiles, GrepFiles, RetrieveContext
from devteam.utils.workspace import read_workspace_file, list_workspace_files, glob_workspace_files, grep_workspace_files

type ToolHandler = Callable[[dict, ProjectState, logging.Logger], Awaitable[str]]

logger = logging.getLogger(__name__)


@dataclass
class ToolEntry:
    schema: type[BaseModel]
    handler: ToolHandler  = None
    enabled_when: Callable[..., bool] = None
    disabled_message: str = None

    def is_enabled(self, settings) -> bool:
        return self.enabled_when is None or self.enabled_when(settings)


class ToolRegistry:
    """Registry mapping tool names to their schema, handler and capability policy."""

    def __init__(self):
        self._entries: dict[str, ToolEntry] = {}

    def register(self, name: str, schema: type[BaseModel], handler: ToolHandler = None, *,
                 enabled_when: Callable[..., bool] = None, disabled_message: str = None):
        self._entries[name] = ToolEntry(schema, handler, enabled_when, disabled_message)

    def get(self, name: str) -> ToolEntry:
        return self._entries.get(name)

    def get_schema(self, name: str) -> type[BaseModel]:
        entry = self._entries.get(name)
        return entry.schema if entry else None

    def get_handler(self, name: str) -> ToolHandler:
        entry = self._entries.get(name)
        return entry.handler if entry else None

    def __contains__(self, name: str) -> bool:
        return name in self._entries

tool_registry = ToolRegistry()


async def _handle_load_skill(tool_args: dict, _state: ProjectState, _logger: logging.Logger) -> str:
    skill_names = tool_args.get('skill_names', [])
    results = []
    for name in skill_names:
        content = skills.load_skill(name)
        _logger.info("Loaded skill: %s", name)
        _logger.debug("Skill Content:\n%s", content[:1000])
        results.append(content)
    return '\n\n---\n\n'.join(results)


async def _handle_retrieve_context(tool_args: dict, _state: ProjectState, _logger: logging.Logger) -> str:
    query = tool_args.get('query', '')
    source = tool_args.get('source')
    _logger.info("Retrieving context for query: %s (source=%s)", query, source)
    chunks = await rag.retrieve_context(query, source=source)
    _logger.debug("Retrieved context:\n%s", chunks[:500])
    return chunks


async def _handle_read_file(tool_args: dict, state: ProjectState, _logger: logging.Logger) -> str:
    path = tool_args.get('path', '')
    _logger.info("Reading workspace file: %s", path)
    return read_workspace_file(path, state.workspace_path)


async def _handle_list_files(_tool_args: dict, state: ProjectState, _logger: logging.Logger) -> str:
    _logger.info("Listing workspace files")
    return list_workspace_files(state.workspace_path)


async def _handle_glob_files(tool_args: dict, state: ProjectState, _logger: logging.Logger) -> str:
    pattern = tool_args.get('pattern', '*')
    _logger.info("Glob workspace files: %s", pattern)
    return glob_workspace_files(pattern, state.workspace_path)


async def _handle_grep_files(tool_args: dict, state: ProjectState, _logger: logging.Logger) -> str:
    pattern = tool_args.get('pattern', '')
    glob_filter = tool_args.get('glob')
    _logger.info("Grep workspace files: %s (glob=%s)", pattern, glob_filter)
    return grep_workspace_files(pattern, state.workspace_path, glob_filter=glob_filter)


_ASK_CLARIFICATION_DISABLED = (
    "The `AskClarification` tool is DISABLED and MUST NOT be called. "
    "Proceed with reasonable assumptions based on the information provided "
    "and call your final output tool directly."
)


def _register_builtins():
    tool_registry.register(LoadSkill.__name__, LoadSkill, _handle_load_skill)
    tool_registry.register(RetrieveContext.__name__, RetrieveContext, _handle_retrieve_context,
                           enabled_when=lambda s: s.rag_enabled)
    tool_registry.register(ReadFile.__name__, ReadFile, _handle_read_file)
    tool_registry.register(ListFiles.__name__, ListFiles, _handle_list_files)
    tool_registry.register(GlobFiles.__name__, GlobFiles, _handle_glob_files)
    tool_registry.register(GrepFiles.__name__, GrepFiles, _handle_grep_files)
    tool_registry.register(AskClarification.__name__, AskClarification,
                           enabled_when=lambda s: not s.no_ask,
                           disabled_message=_ASK_CLARIFICATION_DISABLED)


_register_builtins()
