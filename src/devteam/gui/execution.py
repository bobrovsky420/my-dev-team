import asyncio
from pathlib import Path
import aiosqlite
import yaml
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from devteam import settings
from devteam.utils import LLMFactory, generate_thread_id
from devteam.cli.crew_builder import build_crew
from devteam.extensions import StreamlitLogger, WorkspaceSaver

def get_providers_from_config() -> list[str]:
    config_path = Path('config/llms.yaml')
    if not config_path.exists():
        return ['ollama', 'groq', 'openai']
    try:
        data = yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return list(data['providers'].keys())
    except Exception: # pylint: disable=broad-exception-caught
        return ['ollama', 'groq', 'openai']

def run_crew_in_thread(project_name, requirements, provider, rpm, event_queue, result_holder):
    """Run async crew execution inside a dedicated thread and event loop."""
    async def _inner():
        thread_id = generate_thread_id(project_name)
        project_folder = settings.get_workspaces_dir() / thread_id
        project_folder.mkdir(parents=True, exist_ok=True)
        db_path = project_folder / 'state.db'
        llm_factory = LLMFactory(provider=provider)
        async with aiosqlite.connect(db_path) as conn:
            checkpointer = AsyncSqliteSaver(conn)
            extensions = [
                WorkspaceSaver(workspace_dir=project_folder),
                StreamlitLogger(event_queue),
            ]
            crew = build_crew(llm_factory, checkpointer, rpm, extensions=extensions)
            final_state = await crew.execute(thread_id=thread_id, requirements=requirements)
            result_holder['final_state'] = final_state
            result_holder['thread_id'] = thread_id
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_inner())
    except Exception as exc: # pylint: disable=broad-exception-caught
        result_holder['error'] = str(exc)
    finally:
        loop.close()

def get_existing_threads() -> list[str]:
    if not settings.get_workspaces_dir().exists():
        return []
    return [directory.name for directory in settings.get_workspaces_dir().iterdir() if directory.is_dir()]

async def fetch_history_async(thread_id: str):
    db_path = settings.get_workspaces_dir() / thread_id / 'state.db'
    async with aiosqlite.connect(db_path) as conn:
        checkpointer = AsyncSqliteSaver(conn)
        crew = build_crew(LLMFactory(provider='ollama'), checkpointer)
        return await crew.get_history(thread_id)
