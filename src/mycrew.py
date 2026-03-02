from datetime import datetime
import logging
import re
from dotenv import load_dotenv
from crew import VirtualCrew
from extensions import HumanInTheLoop, WorkspaceSaver

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
    my_extensions = [
        WorkspaceSaver(),
        HumanInTheLoop()
    ]
    project_name, project_requirements = load_project_spec('project.txt')
    thread_id = generate_thread_id(project_name)
    crew = VirtualCrew(extensions=my_extensions)
    final_report = crew.execute_project(requirements=project_requirements, thread_id=thread_id)
    print("\n\n" + "="*50)
    print("PROJECT COMPLETED - FINAL REPORT")
    print("="*50)
    print(final_report)
