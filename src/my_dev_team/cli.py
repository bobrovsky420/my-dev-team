import argparse
import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from my_dev_team import VirtualCrew, ProjectManager, LLMFactory
from my_dev_team.agents import ProductManager, SystemArchitect, SeniorDeveloper, CodeReviewer, QAEngineer, FinalQAEngineer, Reporter
from my_dev_team.extensions import HumanInTheLoop, WorkspaceSaver
from my_dev_team.utils import RateLimiter

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

def build_crew(project_folder: Path, llm_factory: LLMFactory) -> VirtualCrew:
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
        rate_limiter=RateLimiter(requests_per_minute=3)
    )

async def async_main(project_file_path: str, provider: str):
    project_name, project_requirements = load_project_spec(project_file_path)
    thread_id = generate_thread_id(project_name)
    project_folder = Path(f'workspaces/{thread_id}')
    llm_factory = LLMFactory(provider=provider)
    crew = build_crew(project_folder, llm_factory)
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
    parser.add_argument('project_file', help="Path to the text file containing your project requirements")
    parser.add_argument("--provider", type=str, default='ollama', choices=['groq', 'ollama', 'openai'])
    args = parser.parse_args()

    if not Path(args.project_file).exists():
        print(f"❌ Error: Could not find project file '{args.project_file}'")
        exit(1)

    asyncio.run(async_main(args.project_file, args.provider))

if __name__ == '__main__':
    main()
