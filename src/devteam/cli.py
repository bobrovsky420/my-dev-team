import argparse
import asyncio
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import aiosqlite
from rich import print
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from devteam import VirtualCrew, ProjectManager, LLMFactory
from devteam.extensions import HumanInTheLoop, WorkspaceSaver
from devteam.utils import RateLimiter, TelemetryTracker, build_agents_from_config
from devteam import settings

WORKSPACES_DIR = Path('workspaces')
LOG_FILE_NAME = 'mycrew.log'

class ConsoleDispatchFormatter(logging.Formatter):
    """Custom formatter for console output."""
    def __init__(self):
        super().__init__()
        self.root_formatter = logging.Formatter(fmt='%(message)s')
        self.default_formatter = logging.Formatter(fmt='%(name)s: %(message)s')

    def format(self, record):
        if record.name == 'root':
            return self.root_formatter.format(record)
        else:
            return self.default_formatter.format(record)

def setup_logging(verbose = False, *, file_level = logging.DEBUG, console_level = logging.INFO):
    file_handler = logging.FileHandler(LOG_FILE_NAME, encoding='utf-8')
    file_handler.setLevel(file_level)
    if verbose:
        console_level = logging.DEBUG
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(ConsoleDispatchFormatter())
    logging.basicConfig(
        level=logging.DEBUG, # This is the root level
        handlers=[file_handler, console_handler]
    )
    logging.getLogger('aiosqlite').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('LiteLLM').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

def parse_spec_from_string(content: str) -> tuple[str, str]:
    name = 'New Project'
    lines = content.split('\n')
    for line in lines:
        if not line.strip():
            break
        if line.startswith('Subject:') and 'NEW PROJECT:' in line:
            extracted_name = line.split('NEW PROJECT:', 1)[-1].strip()
            if extracted_name:
                name = extracted_name
    return name, content.strip()

def load_project_spec(path: str) -> tuple[str, str]:
    return parse_spec_from_string(Path(path).read_text(encoding='utf-8'))

def generate_thread_id(project_name: str) -> str:
    """Creates a unique, folder-safe thread ID"""
    safe_name = re.sub(r'[^a-z0-9]', '_', project_name.lower())
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_name}_{timestamp}"

def my_extensions(project_folder: Path) -> list:
    return [
        WorkspaceSaver(workspace_dir=project_folder),
        HumanInTheLoop()
    ]

def build_crew(project_folder: Path, llm_factory: LLMFactory, checkpointer: AsyncSqliteSaver, rpm: int = 0) -> VirtualCrew:
    """Instantiates the agents and returns the crew instance"""
    return VirtualCrew(
        manager=ProjectManager(),
        agents=build_agents_from_config('basic.yaml'),
        extensions=my_extensions(project_folder),
        llm_factory=llm_factory,
        checkpointer=checkpointer,
        rate_limiter=RateLimiter(requests_per_minute=rpm) if rpm > 0 else None
    )

async def show_history(thread_id: str = None):
    project_folder = WORKSPACES_DIR / thread_id
    db_path = project_folder / 'state.db'
    llm_factory = LLMFactory(provider='ollama')
    async with aiosqlite.connect(db_path) as conn:
        checkpointer = AsyncSqliteSaver(conn)
        crew = build_crew(project_folder, llm_factory, checkpointer)
        logging.info("🕰️ Fetching timeline history...")
        history_data = await crew.get_history(thread_id)
        for cp in history_data:
            ns_display = cp['ns'].split(':')[0]
            print(ns_display)
            print(f"[{cp['time']}] [{ns_display[:12].center(12)}] Checkpoint: {cp['c_id']} | Next: {cp['node']}")

async def async_main(project_file_path: str, provider: str, rpm: int = 0, resume_thread: str = None, feedback: str = None, feedback_source: str = 'reviewer', checkpoint_id: str = None):
    if resume_thread:
        thread_id = resume_thread
        project_requirements = None
        logging.info("🔄 Resuming existing project thread: %s", thread_id)
    else:
        project_name, project_requirements = load_project_spec(project_file_path)
        thread_id = generate_thread_id(project_name)
        logging.info("🚀 Starting NEW project: %s", project_name)
    project_folder = WORKSPACES_DIR / thread_id
    project_folder.mkdir(parents=True, exist_ok=True)
    db_path = project_folder / 'state.db'
    telemetry = TelemetryTracker()
    llm_factory = LLMFactory(provider=provider, callbacks=[telemetry])
    try:
        async with aiosqlite.connect(db_path) as conn:
            checkpointer = AsyncSqliteSaver(conn)
            crew = build_crew(project_folder, llm_factory, checkpointer, rpm)
            logging.info("🚀 Starting AI Dev Team...")
            logging.info("📁 Workspace: %s", project_folder.absolute())
            final_state = await crew.execute(
                thread_id=thread_id,
                requirements=project_requirements,
                feedback=feedback,
                feedback_source=feedback_source,
                checkpoint_id=checkpoint_id
            )
        if final_state.error:
            logging.error("🛑 Agent framework halted due to an internal error.")
            return
        if final_state.abort_requested:
            logging.error("❌ Workflow aborted by user or validation failure.")
            return
        if final_state.success:
            print("\n🎉 PROJECT COMPLETED SUCCESSFULLY!")
            print(f"Total Revisions: {final_state.total_revisions}\n")
            print(final_state.final_report or "No report generated.")
        else:
            logging.error("🚨 RELEASE FAILED: Integration bugs found!")
            for bug in final_state.integration_bugs:
                print(f" - {bug}")
            print("\nNote: In a production system, these would be appended to the Phase 2 Backlog.")
    except KeyboardInterrupt:
        print((
            "\n\n🛑 Workflow interrupted by user (Ctrl+C)\n"
            "💡 You can resume this exact state later by running:\n"
            f"   devteam --resume {thread_id}"
        ))
    except asyncio.CancelledError:
        logging.error("🛑 Async execution cancelled")
    finally:
        print()
        print(telemetry.get_receipt_panel())
        print(telemetry.get_optimization_panel())
        print()

def launch_ui():
    app_path = Path(__file__).parent / 'app.py'
    logging.info("🚀 Launching My Dev Team Dashboard...")
    subprocess.run([sys.executable, '-m', 'streamlit', 'run', str(app_path)])

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the AI Dev Team autonomous framework.")
    parser.add_argument('project_file', nargs='?', help="path to the text file containing your project requirements")
    parser.add_argument('--config', type=str,  help="path to a custom configuration folder (overrides default one)")
    parser.add_argument('--verbose', action='store_true', help="enable debug logging")
    parser.add_argument('--ui', action='store_true', help="launch the local web dashboard")
    parser.add_argument('--resume', type=str, help="resume a specific thread ID")
    parser.add_argument('--provider', type=str, default='ollama', choices=['groq', 'ollama', 'openai'], help="LLM provider to use (default: ollama)")
    parser.add_argument('--rpm', type=int, default=0, help="API requests per minute (default: 0 = none)")
    parser.add_argument('--feedback', type=str, help="human feedback to inject into the state when resuming")
    parser.add_argument('--as-node', type=str, default='reviewer', choices=['pm', 'architect', 'reviewer', 'qa'], help="which agent should deliver this feedback (forces graph routing)")
    parser.add_argument('--history', action='store_true', help="print the timeline of checkpoints for this thread and exit")
    parser.add_argument('--checkpoint', type=str, help="specific checkpoint ID to rewind to before injecting feedback")
    parser.add_argument('--timeout', type=int, default=120, help="maximum time (in seconds) to wait for an LLM response (default: 120)")

    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.config:
        custom_path = Path(args.config)
        if not custom_path.exists() or not custom_path.is_dir():
            print(f"❌ Error: Config directory '{custom_path}' not found.")
            return
        settings.set_config_dir(custom_path)

    settings.set_llm_timeout(args.timeout)

    if args.ui:
        launch_ui()
        return

    if args.resume:
        path = WORKSPACES_DIR / args.resume
        if not path.exists():
            logging.error("❌ Error: Could not find workspace for thread '%s'", args.resume)
            sys.exit(1)
    elif args.project_file:
        if not Path(args.project_file).exists():
            logging.error("❌ Error: Could not find project file '%s'", args.project_file)
            sys.exit(1)
    else:
        parser.error("You must provide either a project_file OR the --resume flag.")

    if args.history:
        if not args.resume:
            parser.error("--history requires --resume <thread_id> to specify which project to inspect.")
        asyncio.run(show_history(
            thread_id=args.resume,
        ))
        return

    asyncio.run(async_main(
        args.project_file,
        args.provider,
        args.rpm,
        resume_thread=args.resume,
        feedback=args.feedback,
        feedback_source=args.as_node,
        checkpoint_id=args.checkpoint
    ))

if __name__ == '__main__':
    main()
