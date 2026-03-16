import argparse
import asyncio
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
import aiosqlite
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from devteam import VirtualCrew, ProjectManager, LLMFactory
from devteam.agents import ProductManager, SystemArchitect, SeniorDeveloper, CodeReviewer, QAEngineer, FinalQAEngineer, Reporter
from devteam.extensions import HumanInTheLoop, WorkspaceSaver
from devteam.tools import DockerSandbox
from devteam.utils import RateLimiter, TelemetryTracker

WORKSPACES_DIR = Path('workspaces')

def setup_logging(file_level = logging.DEBUG, console_level = logging.INFO):
    file_handler = logging.FileHandler('mycrew.log', encoding='utf-8')
    file_handler.setLevel(file_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s [%(name)s]: %(message)s',
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

def my_agents() -> dict:
    agent_blueprints = {
        'pm': (ProductManager, 'product-manager.md'),
        'architect': (SystemArchitect, 'system-architect.md'),
        'developer': (SeniorDeveloper, 'senior-developer.md'),
        'reviewer': (CodeReviewer, 'code-reviewer.md'),
        'qa': (QAEngineer, 'qa-engineer-sandbox.md'),
        'final_qa': (FinalQAEngineer, 'final-qa-engineer.md'),
        'reporter': (Reporter, 'reporter.md')
    }
    agents = {
        node_name: cls.from_config(node_name, config_file)
        for node_name, (cls, config_file) in agent_blueprints.items()
    }
    agents['qa'] = agents['qa'].with_sandbox(DockerSandbox())
    return agents

def my_extensions(project_folder: Path) -> list:
    return [
        WorkspaceSaver(workspace_dir=project_folder),
        HumanInTheLoop()
    ]

def build_crew(project_folder: Path, llm_factory: LLMFactory, checkpointer: AsyncSqliteSaver, rpm: int = 0) -> VirtualCrew:
    """Instantiates the agents and returns the crew instance"""
    return VirtualCrew(
        manager=ProjectManager(),
        agents=my_agents(),
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
        print("🕰️ Fetching timeline history...")
        history_data = await crew.get_history(thread_id)
        for cp in history_data:
            ns_display = cp['ns'].split(':')[0]
            print(ns_display)
            print(f"[{cp['time']}] [{ns_display[:12].center(12)}] Checkpoint: {cp['c_id']} | Next: {cp['node']}")

async def async_main(project_file_path: str, provider: str, rpm: int = 0, resume_thread: str = None, feedback: str = None, feedback_source: str = 'reviewer', checkpoint_id: str = None):
    if resume_thread:
        thread_id = resume_thread
        project_requirements = None
        print(f"🔄 Resuming existing project thread: {thread_id}")
    else:
        project_name, project_requirements = load_project_spec(project_file_path)
        thread_id = generate_thread_id(project_name)
        print(f"🚀 Starting NEW project: {project_name}")
    project_folder = WORKSPACES_DIR / thread_id
    project_folder.mkdir(parents=True, exist_ok=True)
    db_path = project_folder / 'state.db'
    telemetry = TelemetryTracker()
    llm_factory = LLMFactory(provider=provider, callbacks=[telemetry])
    try:
        async with aiosqlite.connect(db_path) as conn:
            checkpointer = AsyncSqliteSaver(conn)
            crew = build_crew(project_folder, llm_factory, checkpointer, rpm)
            print("🚀 Starting AI Dev Team...")
            print(f"📁 Workspace: {project_folder.absolute()}\n")
            final_state = await crew.execute(
                thread_id=thread_id,
                requirements=project_requirements,
                feedback=feedback,
                feedback_source=feedback_source,
                checkpoint_id=checkpoint_id
            )
        if final_state.abort_requested:
            print("\n❌ Workflow aborted by user or validation failure.")
            return
        if final_state.success:
            print("\n🎉 PROJECT COMPLETED SUCCESSFULLY!")
            print(f"Total Revisions: {final_state.total_revisions}\n")
            print(final_state.final_report or "No report generated.")
        else:
            print("\n🚨 RELEASE FAILED: Integration bugs found!")
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
        print("\n\n🛑 Async execution cancelled")
    finally:
        telemetry.print_receipt()
        telemetry.generate_optimization_report()

def main():
    load_dotenv()
    setup_logging()

    parser = argparse.ArgumentParser(description="Run the AI Dev Team autonomous framework.")
    parser.add_argument('project_file', nargs='?', help="path to the text file containing your project requirements")
    parser.add_argument('--resume', type=str, help="resume a specific thread ID")
    parser.add_argument('--provider', type=str, default='ollama', choices=['groq', 'ollama', 'openai'], help="LLM provider to use (default: ollama)")
    parser.add_argument('--rpm', type=int, default=0, help="API requests per minute (default: 0 = none)")
    parser.add_argument('--feedback', type=str, help="human feedback to inject into the state when resuming")
    parser.add_argument('--as-node', type=str, default='reviewer', choices=['pm', 'architect', 'reviewer', 'qa'], help="which agent should deliver this feedback (forces graph routing)")
    parser.add_argument('--history', action='store_true', help="print the timeline of checkpoints for this thread and exit")
    parser.add_argument('--checkpoint', type=str, help="specific checkpoint ID to rewind to before injecting feedback")

    args = parser.parse_args()

    if args.resume:
        path = WORKSPACES_DIR / args.resume
        if not path.exists():
            print(f"❌ Error: Could not find workspace for thread '{args.resume}'")
            sys.exit(1)
    elif args.project_file:
        if not Path(args.project_file).exists():
            print(f"❌ Error: Could not find project file '{args.project_file}'")
            sys.exit(1)
    else:
        parser.error("You must provide either a project_file OR the --resume flag.")

    if args.history:
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
