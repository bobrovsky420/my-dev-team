from langgraph.graph import StateGraph, START, END
from devteam.crew import ProjectState
from devteam.utils.status import is_approved_status
from .base_manager import BaseManager

class IntegrationManager(BaseManager):
    role = 'Integration Manager'

    def build_graph(self, agents: dict, **kwargs) -> StateGraph:
        workflow = StateGraph(ProjectState)
        workflow.add_node('qa', agents['final_qa'].process)
        workflow.add_node('reporter', agents['reporter'].process)
        workflow.add_edge(START, 'qa')
        workflow.add_conditional_edges('qa', self.route_qa)
        workflow.add_edge('reporter', END)
        return workflow.compile() # No memory here!

    def route_qa(self, state: dict) -> str:
        results = state.get('test_results', '')
        if is_approved_status(results):
            self.logger.debug("Integration tests passed. Proceeding to DevOps.")
            return 'reporter'
        self.logger.error("Integration bugs found! Halting release.")
        return END
