import yaml
from crewai import Task

def create_main_task(project_description: str) -> Task:
    """
    Create a single task for crew manager. The manager will dynamically delegate work to team members as needed.
    """
    file_name = 'agents/manager.yml'
    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
    return Task(
        description=data['backstory'] + '\n\n' + data['goal'] + '\n\n' + data['description'].format(project_description=project_description),
        expected_output=data['expected output']
    )
