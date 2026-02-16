import yaml
from crewai import Agent, Task

def create_tasks(project_description: str, agents: dict[str, Agent]) -> list[Task]:
    """
    Create a list of tasks for the crew based on the project description
    """
    file_name = 'agents/workflow.yml'
    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
    return [
        Task(
            name=task['name'],
            agent=agents[task['agent']],
            description=task['description'].format(project_description=project_description),
            expected_output=task['expected output']
        )
        for task in data.values()
    ]
