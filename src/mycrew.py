from datetime import datetime
import logging
import re
from pathlib import Path
from dotenv import load_dotenv
from agents import ProductManager, SystemArchitect, SeniorDeveloper, CodeJudge, CodeReviewer, QAEngineer, FinalQAEngineer, Reporter
from crew import VirtualCrew
from extensions import HumanInTheLoop, WorkspaceSaver, RateLimiter
from managers import ProjectManager

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

def my_extensions(project_dir: Path) -> list:
    return [
        WorkspaceSaver(workspace_dir=project_dir),
        HumanInTheLoop(),
        RateLimiter(requests_per_minute=1)
    ]

#def my_crew():
#    return VirtualCrew(agents=my_agents(), developers=my_developers(), manager=my_manager(), extensions=my_extensions())

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

    project_crew = VirtualCrew(
        manager=ProjectManager(
            base_thread_id=thread_id,
            project_folder=project_folder,
            extensions=my_extensions(project_folder)
        ),
        agents={
            'pm': ProductManager.from_config('agents/product-manager.md'),
            'architect': SystemArchitect.from_config('agents/system-architect.md'),
            'developer': SeniorDeveloper.from_config('agents/senior-developer.md'),
            'reviewer': CodeReviewer.from_config('agents/code-reviewer.md'),
            'qa': QAEngineer.from_config('agents/qa-engineer.md'),
            'final_qa': FinalQAEngineer.from_config('agents/final-qa-engineer.md'),
            'reporter': Reporter.from_config('agents/reporter.md')
        }
    )
    final_state = project_crew.execute(
        thread_id=f'{thread_id}_lifecycle',
        initial_state={
            'requirements': project_requirements,
            'specs': '',
            'pending_tasks': [],
            'workspace_files': {},
            'final_report': '',
            'integration_bugs': [],
            'communication_log': []
        }
    )
#    if p_log := plan_state.get('communication_log'):
#        global_communication_log.extend(p_log)
#        global_communication_log.append(f"\n### Task {i}: {user_story.split('**')[1] if '**' in user_story else 'Task execution'} ###")
#        if t_log := task_state.get('communication_log'):
#            global_communication_log.extend(t_log)

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
