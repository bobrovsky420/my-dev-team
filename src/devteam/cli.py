import argparse
import asyncio
import logging
import re
import aiosqlite
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from devteam import VirtualCrew, ProjectManager, LLMFactory
from devteam.agents import ProductManager, SystemArchitect, SeniorDeveloper, CodeReviewer, QAEngineer, FinalQAEngineer, Reporter
from devteam.extensions import HumanInTheLoop, WorkspaceSaver
from devteam.utils import RateLimiter

WORKSPACES_DIR = 'workspaces'

def setup_logging():
    file_handler = logging.FileHandler('mycrew.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) # Keep terminal clean, send DEBUG to file
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s [%(name)s]: %(message)s',
        handlers=[file_handler, console_handler]
    )
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

def load_project_spec(path: str) -> tuple[str, str]:
    """Read the project file and return (name, description)"""
    name = 'unknown_project'
    with open(path, encoding='utf-8') as fp:
        for line in fp:
            if not line.strip():
                break
            if line.startswith('Subject:') and 'NEW PROJECT:' in line:
                if extracted_name := line.split('NEW PROJECT:', 1)[-1].strip():
                    name = extracted_name

        fp.seek(0) # Reset pointer to read the full file as requirements
        description = fp.read().strip()
        return name, description

def generate_thread_id(project_name: str) -> str:
    """Creates a unique, folder-safe thread ID"""
    safe_name = re.sub(r'[^a-z0-9]', '_', project_name.lower())
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_name}_{timestamp}"

def build_crew(project_folder: Path, llm_factory: LLMFactory, checkpointer: AsyncSqliteSaver, rpm: int = 0) -> VirtualCrew:
    """Instantiates the agents and returns the crew instance"""
    agents = {
        'pm': ProductManager.from_config('product-manager.md'),
        'architect': SystemArchitect.from_config('system-architect.md'),
        'developer': SeniorDeveloper.from_config('senior-developer.md'),
        'reviewer': CodeReviewer.from_config('code-reviewer.md'),
        'qa': QAEngineer.from_config('qa-engineer.md'),
        'final_qa': FinalQAEngineer.from_config('final-qa-engineer.md'),
        'reporter': Reporter.from_config('reporter.md')
    }
    extensions = [
        WorkspaceSaver(workspace_dir=project_folder),
        HumanInTheLoop()
    ]
    return VirtualCrew(
        manager=ProjectManager(),
        agents=agents,
        extensions=extensions,
        llm_factory=llm_factory,
        checkpointer=checkpointer,
        rate_limiter=RateLimiter(requests_per_minute=rpm) if rpm > 0 else None
    )

async def async_main(project_file_path: str, provider: str, rpm: int = 0, resume_thread: str = None):
    if resume_thread:
        thread_id = resume_thread
        project_requirements = None
        print(f"🔄 Resuming existing project thread: {thread_id}")
    else:
        project_name, project_requirements = load_project_spec(project_file_path)
        thread_id = generate_thread_id(project_name)
        print(f"🚀 Starting NEW project: {project_name}")
    project_folder = Path(f'{WORKSPACES_DIR}/{thread_id}')
    project_folder.mkdir(parents=True, exist_ok=True)
    db_path = project_folder / 'state.db'
    llm_factory = LLMFactory(provider=provider)
    async with aiosqlite.connect(db_path) as conn:
        checkpointer = AsyncSqliteSaver(conn)
        crew = build_crew(project_folder, llm_factory, checkpointer, rpm)
        print(f"🚀 Starting AI Dev Team...")
        print(f"📁 Workspace: {project_folder.absolute()}\n")
        final_state = await crew.execute(
            thread_id=thread_id,
            requirements=project_requirements
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

def main():
    load_dotenv()
    setup_logging()

    parser = argparse.ArgumentParser(description="Run the AI Dev Team autonomous framework.")
    parser.add_argument('project_file', nargs='?', help="path to the text file containing your project requirements")
    parser.add_argument('--resume', type=str, help="resume a specific thread ID")
    parser.add_argument('--provider', type=str, default='ollama', choices=['groq', 'ollama', 'openai'], help="LLM provider to use (default: ollama)")
    parser.add_argument('--rpm', type=int, default=0, help="API requests per minute (default: 0 = none)")

    args = parser.parse_args()

    if args.resume:
        if not Path(f'{WORKSPACES_DIR}/{args.resume}').exists():
            print(f"❌ Error: Could not find workspace for thread '{args.resume}'")
            exit(1)
    elif args.project_file:
        if not Path(args.project_file).exists():
            print(f"❌ Error: Could not find project file '{args.project_file}'")
            exit(1)
    else:
        parser.error("You must provide either a project_file OR the --resume flag.")

    asyncio.run(async_main(args.project_file, args.provider, args.rpm, resume_thread=args.resume))

if __name__ == '__main__':
    main()
