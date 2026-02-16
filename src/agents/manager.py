import importlib
import yaml
from crewai import Agent, Task

project_schema = importlib.import_module('project.schema')

def create_tasks(agents: dict[str, Agent]) -> list[Task]:
    """
    Create a list of tasks for the crew based on the project description
    """
    file_name = 'agents/workflow.yml'
    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
    return [new_task(task, agents) for task in data.values()]

def new_task(data: dict, agents: dict[str, Agent]) -> Task:
    task_config = {
        'name': data['name'],
        'agent': agents[data['agent']],
        'description': data['description'],
        'expected_output': data['expected output'],
    }
    if 'output pydantic' in data:
        task_config['output_pydantic'] = getattr(project_schema, data['output pydantic'])
    return Task(**task_config)
