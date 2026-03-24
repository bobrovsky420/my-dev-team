import asyncio
import aiosqlite
import yaml
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from devteam import settings
from devteam.utils import LLMFactory, StreamHandler, generate_thread_id
from devteam.crew import CrewFactory
from devteam.extensions import StreamlitLogger

def get_providers_from_config() -> list[str]:
    config_path = settings.get_config_dir() / 'llms.yaml'
    if not config_path.exists():
        return ['ollama', 'groq', 'openai']
    try:
        data = yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return list(data['providers'].keys())
    except Exception: # pylint: disable=broad-exception-caught
        return ['ollama', 'groq', 'openai']

def run_crew_in_thread(project_name, requirements, provider, rpm, event_queue, result_holder, hitl_extension=None, thinking=False):
    """Run async crew execution inside a dedicated thread and event loop."""
    async def _inner():
        thread_id = generate_thread_id(project_name)
        project_folder = settings.get_workspaces_dir() / thread_id
        project_folder.mkdir(parents=True, exist_ok=True)
        db_path = project_folder / 'state.db'
        callbacks = []
        settings.set_llm_streaming(thinking)
        if thinking:
            callbacks.append(StreamHandler(queue=event_queue))
        llm_factory = LLMFactory(provider=provider, callbacks=callbacks)
        crew_factory = CrewFactory(llm_factory=llm_factory)
        extensions = [
            StreamlitLogger(event_queue),
        ]
        if hitl_extension:
            extensions.append(hitl_extension)
        async with aiosqlite.connect(db_path) as conn:
            checkpointer = AsyncSqliteSaver(conn)
            crew = crew_factory.create(project_folder, checkpointer=checkpointer, rpm=rpm, extensions=extensions)
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
        project_folder = settings.get_workspaces_dir() / thread_id
        checkpointer = AsyncSqliteSaver(conn)
        crew_factory = CrewFactory()
        crew = crew_factory.create(project_folder, checkpointer=checkpointer)
        return await crew.get_history(thread_id)
