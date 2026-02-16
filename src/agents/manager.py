import importlib
import yaml
from crewai import Agent, Task

def create_tasks(agents: dict[str, Agent]) -> list[Task]:
    """
    Create a list of tasks for the crew based on the project description
    """
    file_name = 'agents/workflow.yml'
    project_schema = importlib.import_module('project.schema')
    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
    return [
        Task(
            name=task['name'],
            agent=agents[task['agent']],
            description=task['description'],
            expected_output=task['expected output'],
            output_pydantic=getattr(project_schema, task['output pydantic']) if 'output pydantic' in task else None
        )
        for task in data.values()
    ]
