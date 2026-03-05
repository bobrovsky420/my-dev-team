from langgraph.graph import StateGraph, START, END
from state import ExecutionState
from .base_manager import BaseManager

class StandardExecutionManager(BaseManager):
    """Executes a single ticket using one developer."""
    def build_graph(self, agents: dict, memory) -> StateGraph:
        workflow = StateGraph(ExecutionState)
        workflow.add_node('developer', agents['developer'].process)
        workflow.add_node('reviewer', agents['reviewer'].process)
        workflow.add_node('qa', agents['qa'].process)
        workflow.add_edge(START, 'developer')
        workflow.add_edge('developer', 'reviewer')
        workflow.add_conditional_edges('reviewer', self.route_reviewer)
        workflow.add_conditional_edges('qa', self.route_qa)
        return workflow.compile(checkpointer=memory)

    def route_reviewer(self, state: dict) -> str:
        feedback = state.get('review_feedback', '').strip().strip('.')
        if feedback.upper() == 'APPROVED':
            return 'qa'
        if state.get('revision_count', 0) >= 3:
            self.logger.warning("Max revisions reached. Forcing completion.")
            return END
        return 'developer'

    def route_qa(self, state: dict) -> str:
        results = state.get('test_results', '').strip().strip('.')
        if results.upper() == 'PASSED':
            self.logger.info("Task '%s' passed all checks!", state.get('current_task'))
            return END
        if state.get('revision_count', 0) >= 3:
            self.logger.warning("Max revisions reached. Forcing completion.")
            return END
        return 'developer'
