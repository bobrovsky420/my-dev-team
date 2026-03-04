from datetime import datetime
import logging
import re
from dotenv import load_dotenv
from agents import ProductManager, SystemArchitect, SeniorDeveloper, CodeJudge, CodeReviewer, QAEngineer, QAFinal, Reporter
from crew import VirtualCrew
from extensions import HumanInTheLoop, WorkspaceSaver, RateLimiter
from managers.abmanager import ABManager

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

def my_agents():
    return {
        'pm': ProductManager.from_config('agents/product-manager.md'),
        'architect': SystemArchitect.from_config('agents/system-architect.md'),
        'judge': CodeJudge.from_config('agents/code-judge.md'),
        'reviewer': CodeReviewer.from_config('agents/code-reviewer.md'),
        'qa': QAEngineer.from_config('agents/qa-engineer.md'),
        'final-qa': QAFinal.from_config('agents/final-qa-engineer.md'),
        'reporter': Reporter.from_config('agents/reporter.md')
    }

def my_developers():
    name = 'dev'
    devs = SeniorDeveloper.from_config('agents/senior-developer.md')
    if isinstance(devs, list):
        return {f'{name}_{i+1}': dev for i, dev in enumerate(devs)}
    return {name: devs}

def my_extensions():
    return [
        WorkspaceSaver(),
        HumanInTheLoop(),
        RateLimiter()
    ]

def my_manager():
    return ABManager(developers=list(my_developers().keys()))

def my_crew():
    return VirtualCrew(agents=my_agents(), developers=my_developers(), manager=my_manager(), extensions=my_extensions())

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
    crew = my_crew()
    final_report = crew.execute_project(requirements=project_requirements, thread_id=thread_id)
    print("\n\n" + "="*50)
    print("PROJECT COMPLETED - FINAL REPORT")
    print("="*50)
    print(final_report)
