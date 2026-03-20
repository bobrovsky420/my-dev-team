from langgraph.graph import StateGraph, START, END
from devteam.state import ProjectState
from devteam.utils.status import is_approved_status
from .base_manager import BaseManager

class StandardExecutionManager(BaseManager):
    def __init__(self, max_revision_count: int = 3):
        super().__init__()
        self.max_revision_count = max_revision_count

    def build_graph(self, agents: dict, **kwargs) -> StateGraph:
        workflow = StateGraph(ProjectState)
        workflow.add_node('developer', agents['developer'].process)
        workflow.add_node('reviewer', agents['reviewer'].process)
        workflow.add_node('qa', agents['qa'].process)
        workflow.add_edge(START, 'developer')
        workflow.add_edge('developer', 'reviewer')
        workflow.add_conditional_edges('reviewer', self.route_reviewer)
        workflow.add_conditional_edges('qa', self.route_qa)
        return workflow.compile()

    def route_reviewer(self, state: dict) -> str:
        feedback = state.get('review_feedback', '')
        if is_approved_status(feedback):
            return 'qa'
        if state.get('revision_count', 0) >= self.max_revision_count:
            self.logger.warning("Max revisions reached. Forcing completion.")
            return END
        return 'developer'

    def route_qa(self, state: dict) -> str:
        results = state.get('test_results', '')
        if is_approved_status(results):
            self.logger.debug("Task '%s' passed all checks!", state.get('current_task'))
            return END
        if state.get('revision_count', 0) >= self.max_revision_count:
            self.logger.warning("Max revisions reached. Forcing completion.")
            return END
        return 'developer'
