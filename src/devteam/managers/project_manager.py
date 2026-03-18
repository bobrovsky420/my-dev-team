from typing import Any
from langgraph.graph import StateGraph, START, END
from devteam.crew import ProjectState
from devteam.utils import task_to_markdown
from .base_manager import BaseManager
from .planning_manager import PlanningManager
from .execution_manager import StandardExecutionManager
from .integration_manager import IntegrationManager

class ProjectManager(BaseManager):
    role = 'Project Manager'

    def build_graph(self, agents: dict, memory: Any = None) -> StateGraph: # pylint: disable=arguments-differ
        self.agents = agents
        workflow = StateGraph(ProjectState)
        planning_graph = PlanningManager().build_graph(agents)
        development_graph = StandardExecutionManager().build_graph(agents)
        integration_graph = IntegrationManager().build_graph(agents)
        workflow.add_node('planning', planning_graph)
        workflow.add_node('officer', self.route_tasks_node)
        workflow.add_node('development', development_graph)
        workflow.add_node('integration', integration_graph)
        workflow.add_edge(START, 'planning')
        workflow.add_conditional_edges('planning', self.route_after_planning)
        workflow.add_conditional_edges('officer', self.edge_from_router)
        workflow.add_edge('development', 'officer')
        workflow.add_edge('integration', END)
        return workflow.compile(checkpointer=memory)

    def route_after_planning(self, state: dict) -> str:
        if state.get('abort_requested'):
            self.logger.debug("Stopping lifecycle graph after planning abort.")
            return END
        if not state.get('pending_tasks'):
            self.logger.debug("No backlog pending, stopping lifecycle graph")
            return END
        return 'officer'

    def route_tasks_node(self, state: dict) -> dict:
        pending = state.get('pending_tasks', [])
        idx = state.get('current_task_index', 0)
        current_revisions = state.get('revision_count', 0)
        if idx < len(pending):
            task = pending[idx]
            t_name = task.get('task_name', f'Task {idx+1}')
            formatted_task = task_to_markdown(task, idx + 1)
            self.logger.info("Routing to Task %i/%i: %s", idx + 1, len(pending), t_name)
            return {
                'current_phase': 'development',
                'current_task': formatted_task,
                'current_task_index': idx + 1,
                'total_revisions': current_revisions, # Pass task revisions to total aggregator
                'revision_count': 0,                  # Reset loop counter for new task
                'review_feedback': '',
                'test_results': '',
                'communication_log': [f"\n### Task {idx + 1}: {t_name} ###"]
            }
        self.logger.info("Execution phase completed. Routing to integration.")
        return {
            'current_phase': 'integration',
            'current_task': '',
            'total_revisions': current_revisions,
        }

    def edge_from_router(self, state: dict) -> str:
        if state.get('abort_requested'):
            return END
        return state.get('current_phase')
