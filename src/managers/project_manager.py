from pathlib import Path
from langgraph.graph import StateGraph, START, END
from crew import VirtualCrew
from state import ProjectLifecycleState
from .base_manager import BaseManager
from .planning_manager import PlanningManager
from .execution_manager import StandardExecutionManager
from .integration_manager import IntegrationManager

class ProjectManager(BaseManager):
    role = 'Project Manager'

    def __init__(self, base_thread_id: str, project_folder: Path, extensions: list):
        super().__init__()
        self.base_thread_id = base_thread_id
        self.project_folder = project_folder
        self.extensions = extensions

    def build_graph(self, agents: dict, memory) -> StateGraph:
        self.agents = agents
        workflow = StateGraph(ProjectLifecycleState)
        workflow.add_node('planning', self.run_planning)
        workflow.add_node('development', self.run_development)
        workflow.add_node('integration', self.run_integration)
        workflow.add_edge(START, 'planning')
        workflow.add_conditional_edges('planning', self.route_after_planning)
        workflow.add_conditional_edges('development', self.route_after_development)
        workflow.add_edge('integration', END)
        return workflow.compile(checkpointer=memory)

    def run_planning(self, state: dict) -> dict:
        planning_crew = VirtualCrew(
            manager=PlanningManager(),
            agents={
                'pm': self.agents['pm'],
                'architect': self.agents['architect']
            },
            extensions=self.extensions
        )
        plan_state = planning_crew.execute(
            thread_id=f'{self.base_thread_id}_plan',
            initial_state={
                'requirements': state.get('requirements', ''),
                'communication_log': []
            }
        )
        updates = {
            'specs': plan_state.get('specs', ''),
            'pending_tasks': plan_state.get('pending_tasks', ''),
            'communication_log': plan_state.get('communication_log', []) + [f"**[{self.name or self.role}]**: Planning phase completed."]
        }
        if plan_state.get('abort_requested'):
            updates['abort_requested'] = True
        return updates

    def run_development(self, state: dict) -> dict:
        backlog = state.get('pending_tasks', [])
        current_workspace = state.get('workspace_files', {}).copy()
        total_revisions = 0
        execution_logs: list[str] = []
        execution_crew = VirtualCrew(
            manager=StandardExecutionManager(),
            agents={
                'developer': self.agents['developer'],
                'reviewer': self.agents['reviewer'],
                'qa': self.agents['qa']
            },
            extensions=self.extensions
        )
        for i, user_story in enumerate(backlog, start=1):
            self.logger.info("Starting task %i/%i", i, len(backlog))
            task_state = execution_crew.execute(
                thread_id=f'{self.base_thread_id}_task_{i}',
                initial_state={
                    'specs': state.get('specs', ''),
                    'current_task': user_story,
                    'workspace_files': current_workspace,
                    'review_feedback': '',
                    'test_results': '',
                    'revision_count': 0,
                    'communication_log': []
                }
            )
            if task_state.get('abort_requested'):
                return {
                    'abort_requested': True,
                    'workspace_files': current_workspace,
                    'communication_log': execution_logs + [f"**[{self.name or self.role}]**: Execution aborted at task {i}."]
                }
            current_workspace = task_state.get('workspace_files', current_workspace)
            total_revisions += task_state.get('revision_count', 0)
            execution_logs.extend(task_state.get('communication_log', []))
        return {
            'workspace_files': current_workspace,
            'total_revisions': total_revisions,
            'communication_log': execution_logs + [f"**[{self.name or self.role}]**: Execution phase completed ({len(backlog)} tasks)."]
        }

    def run_integration(self, state: dict) -> dict:
        current_workspace = state.get('workspace_files', {})
        integration_crew = VirtualCrew(
            manager=IntegrationManager(),
            agents={
                'qa': self.agents['final_qa'],
                'reporter': self.agents['reporter']
            },
            extensions=self.extensions
        )
        final_state = integration_crew.execute(
            thread_id=f'{self.base_thread_id}_integration',
            initial_state={
                'requirements': state.get('requirements', ''),
                'specs': state.get('specs', ''),
                'workspace_files': current_workspace,
                'total_revisions': state.get('total_revisions', 0),
                'communication_log': state.get('communication_log', []).copy()
            }
        )
        updates = {
            'final_report': final_state.get('final_report', 'No report generated.'),
            'integration_bugs': final_state.get('integration_bugs', []),
            'communication_log': final_state.get('communication_log', []) + [f"**[{self.name or self.role}]**: Integration phase completed."]
        }
        if final_state.get('abort_requested'):
            updates['abort_requested'] = True
        return updates

    def route_after_planning(self, state: dict) -> str:
        if state.get('abort_requested'):
            self.logger.info("Stopping lifecycle graph after planning abort.")
            return END
        if not state.get('pending_tasks'):
            self.logger.info("No backlog pending, stopping lifecycle graph")
            return END
        return 'development'

    def route_after_development(self, state: dict) -> str:
        if state.get('abort_requested'):
            self.logger.info("Stopping lifecycle graph after development abort.")
            return END
        return 'integration'
