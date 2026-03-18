import asyncio
import logging
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from rich import print # pylint: disable=redefined-builtin
from devteam import settings
from devteam.utils import LLMFactory, TelemetryTracker, generate_thread_id, load_project_spec
from .crew_builder import build_crew, my_extensions

STATE_DB_FILE = 'state.db'

async def show_history(thread_id: str):
    project_folder = settings.get_workspaces_dir() / thread_id
    db_path = project_folder / STATE_DB_FILE
    llm_factory = LLMFactory(provider='ollama')
    async with aiosqlite.connect(db_path) as conn:
        checkpointer = AsyncSqliteSaver(conn)
        crew = build_crew(project_folder, llm_factory, checkpointer)
        logging.info("Fetching timeline history...")
        history_data = await crew.get_history(thread_id)
        for checkpoint in history_data:
            ns_display = checkpoint['ns'].split(':')[0]
            print(ns_display)
            print(
                f"[{checkpoint['time']}] "
                f"[{ns_display[:12].center(12)}] "
                f"Checkpoint: {checkpoint['c_id']} | Next: {checkpoint['node']}"
            )

async def async_main(project_file_path: str, provider: str, rpm: int = 0, resume_thread: str = None, feedback: str = None, feedback_source: str = 'reviewer', checkpoint_id: str = None):
    if resume_thread:
        thread_id = resume_thread
        project_requirements = None
        logging.info('🔄 Resuming existing project thread: %s', thread_id)
    else:
        project_name, project_requirements = load_project_spec(project_file_path)
        thread_id = generate_thread_id(project_name)
        logging.info('🚀 Starting NEW project: %s', project_name)
    project_folder = settings.get_workspaces_dir() / thread_id
    project_folder.mkdir(parents=True, exist_ok=True)
    db_path = project_folder / 'state.db'
    telemetry = TelemetryTracker()
    llm_factory = LLMFactory(provider=provider, callbacks=[telemetry])
    try:
        async with aiosqlite.connect(db_path) as conn:
            checkpointer = AsyncSqliteSaver(conn)
            crew = build_crew(
                project_folder,
                llm_factory,
                checkpointer,
                rpm=rpm,
                extensions=my_extensions()
            )
            logging.info('🚀 Starting AI Dev Team...')
            logging.info('📁 Workspace: %s', project_folder.absolute())
            final_state = await crew.execute(
                thread_id=thread_id,
                requirements=project_requirements,
                feedback=feedback,
                feedback_source=feedback_source,
                checkpoint_id=checkpoint_id,
            )
        if final_state.error:
            logging.error('🛑 Agent framework halted due to an internal error.')
            return
        if final_state.abort_requested:
            logging.error('❌ Workflow aborted by user or validation failure.')
            return
        if final_state.success:
            print('\n🎉 PROJECT COMPLETED SUCCESSFULLY!')
            print(f'Total Revisions: {final_state.total_revisions}\n')
            print(final_state.final_report or 'No report generated.')
            return
        logging.error('🚨 RELEASE FAILED: Integration bugs found!')
        for bug in final_state.integration_bugs:
            print(f' - {bug}')
        print('\nNote: In a production system, these would be appended to the Phase 2 Backlog.')
    except KeyboardInterrupt:
        print(
            '\n\n🛑 Workflow interrupted by user (Ctrl+C)\n'
            '💡 You can resume this exact state later by running:\n'
            f'   devteam --resume {thread_id}'
        )
    except asyncio.CancelledError:
        logging.error('🛑 Async execution cancelled')
    finally:
        print()
        print(telemetry.get_receipt_panel())
        print(telemetry.get_optimization_panel())
        print()
