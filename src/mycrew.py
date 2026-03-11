from datetime import datetime
import logging
import re
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from my_dev_team import VirtualCrew, ProjectManager
from my_dev_team.agents import ProductManager, SystemArchitect, SeniorDeveloper, CodeJudge, CodeReviewer, QAEngineer, FinalQAEngineer, Reporter
from my_dev_team.extensions import HumanInTheLoop, WorkspaceSaver
from my_dev_team.utils import RateLimiter

load_dotenv()

LOG_FILE = 'mycrew.log'

file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(name)s]: %(message)s',
    handlers=[
        file_handler,
        console_handler
    ]
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

def my_agents() -> dict:
    return {
        'pm': ProductManager.from_config('product-manager.md'),
        'architect': SystemArchitect.from_config('system-architect.md'),
        'developer': SeniorDeveloper.from_config('senior-developer.md'),
        'reviewer': CodeReviewer.from_config('code-reviewer.md'),
        'qa': QAEngineer.from_config('qa-engineer.md'),
        'final_qa': FinalQAEngineer.from_config('final-qa-engineer.md'),
        'reporter': Reporter.from_config('reporter.md')
    }

def my_extensions(project_dir: Path) -> list:
    return [
        WorkspaceSaver(workspace_dir=project_dir),
        HumanInTheLoop()
    ]

def my_crew(project_folder):
    return VirtualCrew(
        manager=ProjectManager(),
        agents=my_agents(),
        extensions=my_extensions(project_folder),
        rate_limiter=RateLimiter(requests_per_minute=3)
    )

def load_project_spec(path: str = 'project.txt') -> tuple[str, str]:
    """Read the project file and return (name, description)."""
    name = 'unknown_project'
    with open(path, encoding='utf-8') as fp:
        for line in fp:
            if not line.strip():
                break
            if line.startswith('Subject:') and 'NEW PROJECT:' in line:
                if extracted_name := line.split('NEW PROJECT:', 1)[-1].strip():
                    name = extracted_name
        description = fp.read().strip()
        return name, description

def generate_thread_id(project_name: str) -> str:
    """Creates a unique, folder-safe thread ID (e.g., 'web_scraper_20260124_153022')."""
    safe_name = re.sub(r'[^a-z0-9]', '_', project_name.lower())
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_name}_{timestamp}"

if __name__ == '__main__':
    project_name, project_requirements = load_project_spec('project.txt')
    thread_id = generate_thread_id(project_name)
    project_folder = Path(f'workspaces/{thread_id}')
    project_crew = my_crew(project_folder)
    final_state = asyncio.run(project_crew.execute(
        thread_id=thread_id,
        requirements=project_requirements
    ))
    if final_state.get('abort_requested'):
        print("❌ Workflow aborted by user or validation failure.")
        exit(0)
    if not final_state.get('pending_tasks'):
        print("❌ System architect failed to generate a backlog.")
        exit(1)
    final_report = final_state.get('final_report', 'No report generated.')
    integration_bugs = final_state.get('integration_bugs', [])
    if integration_bugs:
        print("\n🚨 RELEASE FAILED: Integration bugs found!")
        for bug in integration_bugs:
            print(f" - {bug}")
        print("Note: In a production system, these would be automatically appended to the Phase 2 Backlog.")
    else:
        print("\n🎉 PROJECT COMPLETED SUCCESSFULLY!")
        print(final_report)
