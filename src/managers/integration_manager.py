from langgraph.graph import StateGraph, START, END
from state import IntegrationState
from .base_manager import BaseManager

class IntegrationManager(BaseManager):
    role = 'Integration Manager'

    def build_graph(self, agents: dict, developers: dict, memory, human_interrupter) -> StateGraph:
        workflow = StateGraph(IntegrationState)
        workflow.add_node('qa', agents['qa'].process)
#        workflow.add_node('devops', agents['devops'].process)
        workflow.add_node('reporter', agents['reporter'].process)
        workflow.add_edge(START, 'qa')
        workflow.add_conditional_edges('qa', self.route_qa)
#        workflow.add_edge('devops', 'reporter')
        workflow.add_edge('reporter', END)
        return workflow.compile(checkpointer=memory)

    def route_qa(self, state: dict) -> str:
        results = state.get('test_results', '').strip().strip('.')
        if results.upper() == 'PASSED':
            self.logger.info("Integration tests passed. Proceeding to DevOps.")
            return 'reporter'
#            return 'devops'
        self.logger.error("Integration bugs found! Halting release.")
        return END
