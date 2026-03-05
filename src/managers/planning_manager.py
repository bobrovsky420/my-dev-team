from langgraph.graph import StateGraph, START, END
from state import PlanningState
from .base_manager import BaseManager

class PlanningManager(BaseManager):
    role = 'Planning Manager'

    def build_graph(self, agents: dict, developers: dict, memory, human_interrupter) -> StateGraph:
        workflow = StateGraph(PlanningState)
        workflow.add_node('human', human_interrupter)
        workflow.add_node('pm', agents['pm'].process)
        workflow.add_node('architect', agents['architect'].process)
        workflow.add_conditional_edges(START, self.route_start)
        workflow.add_conditional_edges('human', self.route_start)
        workflow.add_conditional_edges('pm', self.route_start)
        workflow.add_edge('architect', END)
        return workflow.compile(checkpointer=memory, interrupt_before=['human'])

    def route_start(self, state: dict) -> str:
        self.logger.info("Routing Planning Phase...")
        if state.get('clarification_question'):
            return 'human'
        if not state.get('specs'):
            return 'pm'
        if not state.get('pending_tasks'):
            return 'architect'
        return END
