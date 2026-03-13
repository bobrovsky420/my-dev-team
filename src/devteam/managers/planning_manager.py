from langgraph.graph import StateGraph, START, END
from ..crew import ProjectState
from .base_manager import BaseManager

class PlanningManager(BaseManager):
    role = 'Planning Manager'

    def build_graph(self, agents: dict, **kwargs) -> StateGraph:
        workflow = StateGraph(ProjectState)
        workflow.add_node('human', self.dummy_human_node)
        workflow.add_node('pm', agents['pm'].process)
        workflow.add_node('architect', agents['architect'].process)
        workflow.add_conditional_edges(START, self.route_start)
        workflow.add_conditional_edges('human', self.route_start)
        workflow.add_conditional_edges('pm', self.route_start)
        workflow.add_edge('architect', END)
        return workflow.compile(interrupt_before=['human'])

    def dummy_human_node(self, state: dict) -> dict:
        self.logger.info("Human input received. Resuming workflow...")
        return {'clarification_question': ''}

    def route_start(self, state: dict) -> str:
        self.logger.info("Routing Planning Phase...")
        if state.get('clarification_question'):
            return 'human'
        if not state.get('specs'):
            return 'pm'
        if not state.get('pending_tasks'):
            return 'architect'
        return END
