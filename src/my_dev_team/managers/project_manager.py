from langgraph.graph import StateGraph, START, END
from ..state import ProjectState
from .base_manager import BaseManager
from .planning_manager import PlanningManager
from .execution_manager import StandardExecutionManager
from .integration_manager import IntegrationManager

class ProjectManager(BaseManager):
    role = 'Project Manager'

    def build_graph(self, agents: dict, memory = None) -> StateGraph: # pylint: disable=arguments-differ
        self.agents = agents
        workflow = StateGraph(ProjectState)
        planning_graph = PlanningManager().build_graph(agents)
        development_graph = StandardExecutionManager().build_graph(agents)
        integration_graph = IntegrationManager().build_graph(agents)
        workflow.add_node('planning', planning_graph)
        workflow.add_node('task_router', self.route_tasks_node)
        workflow.add_node('development', development_graph)
        workflow.add_node('integration', integration_graph)
        workflow.add_edge(START, 'planning')
        workflow.add_conditional_edges('planning', self.route_after_planning)
        workflow.add_conditional_edges('task_router', self.edge_from_router)
        workflow.add_edge('development', 'task_router')
        workflow.add_edge('integration', END)
        return workflow.compile(checkpointer=memory)

    def route_after_planning(self, state: dict) -> str:
        if state.get('abort_requested'):
            self.logger.info("Stopping lifecycle graph after planning abort.")
            return END
        if not state.get('pending_tasks'):
            self.logger.info("No backlog pending, stopping lifecycle graph")
            return END
        return 'task_router'

    def route_tasks_node(self, state: dict) -> dict:
        pending = state.get('pending_tasks', [])
        idx = state.get('current_task_index', 0)
        current_revisions = state.get('revision_count', 0)
        if idx < len(pending):
            task = pending[idx]
            self.logger.info("Routing to Task %i/%i", idx + 1, len(pending))
            return {
                'current_task': task,
                'current_task_index': idx + 1,
                'total_revisions': current_revisions,
                'revision_count': 0,
                'review_feedback': '',
                'test_results': '',
                'communication_log': [f"\n### Task {idx + 1}: {task.split('**')[1] if '**' in task else 'Task execution'} ###"]
            }
        self.logger.info("Execution phase completed. Routing to integration.")
        return {
            'current_task': 'ALL_DONE',
            'total_revisions': current_revisions,
        }

    def edge_from_router(self, state: dict) -> str:
        if state.get('abort_requested'):
            return END
        if state.get('current_task') == 'ALL_DONE':
            return 'integration'
        return 'development'
