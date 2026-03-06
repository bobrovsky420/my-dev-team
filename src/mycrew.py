from datetime import datetime
import logging
import re
from dotenv import load_dotenv
from agents import ProductManager, SystemArchitect, SeniorDeveloper, CodeJudge, CodeReviewer, QAEngineer, FinalQAEngineer, Reporter
from crew import VirtualCrew
from extensions import HumanInTheLoop, WorkspaceSaver, RateLimiter
from managers import PlanningManager, StandardExecutionManager, IntegrationManager

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

def my_extensions():
    return [
        WorkspaceSaver(),
        HumanInTheLoop(),
#        RateLimiter()
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
    # PLANNING
    planning_crew = VirtualCrew(manager=PlanningManager(), agents={
        'pm': ProductManager.from_config('agents/product-manager.md'),
        'architect': SystemArchitect.from_config('agents/system-architect.md')
    }, extensions=my_extensions())
    plan_state = planning_crew.execute(thread_id=thread_id, initial_state={
        'requirements': project_requirements,
        'communication_log': []
    })
    # EXECUTION
    project_specs = plan_state.get('specs', '')
    backlog = plan_state.get('pending_tasks', [])
    if not backlog:
        print("❌ Error: System Architect failed to generate a backlog. Exiting.")
        exit(1)
    current_codebase = ''
    execution_crew = VirtualCrew(manager=StandardExecutionManager(), agents={
        'developer': SeniorDeveloper.from_config('agents/senior-developer.md'),
        'reviewer': CodeReviewer.from_config('agents/code-reviewer.md'),
        'qa': QAEngineer.from_config('agents/qa-engineer.md')
    }, extensions=my_extensions())
    for i, user_story in enumerate(backlog, start=1):
        print(f"\n--- 🎫 Starting Ticket {i}/{len(backlog)} ---")
        task_state = execution_crew.execute(
            thread_id=f'{thread_id}_task_{i}',
            initial_state={
                'specs': project_specs,
                'current_task': user_story,
                'existing_code': current_codebase,
                'revision_count': 0,
                'communication_log': []
            }
        )
        current_codebase = task_state.get('code', current_codebase)
    # INTEGRATION
    integration_crew = VirtualCrew(manager=IntegrationManager(), agents={
        'qa': FinalQAEngineer.from_config('agents/final-qa-engineer.md'),
        'reporter': Reporter.from_config('agents/reporter.md')
    }, extensions=my_extensions())
    final_state = integration_crew.execute(
        thread_id=f'{thread_id}_release',
        initial_state={
            'requirements': project_requirements,
            'specs': project_specs,
            'code': current_codebase,
            'communication_log': []
        }
    )
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
