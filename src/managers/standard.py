from langgraph.graph import StateGraph, START, END
from crew.project import ProjectState
from .base import BaseManager

class StandardManager(BaseManager):
    def build_graph(self, agents: dict, developers: dict, memory, human_interrupter):
        """
        ```mermaid
        stateDiagram-v2
            [*] --> pm
            pm --> human
            human --> pm
            pm --> architect
            architect --> officer
            officer --> dev
            dev --> reviewer
            reviewer --> dev
            reviewer --> qa
            qa --> dev
            qa --> officer
            officer --> final_qa
            final_qa --> reporter
            reporter --> [*]
        ```
        """
        workflow = StateGraph(ProjectState)
        for name in agents:
            workflow.add_node(name, agents[name].process)
        for name in developers:
            workflow.add_node(name, developers[name].process)
        workflow.add_node('officer', self.queue_manager)
        workflow.add_node('human', human_interrupter)
        workflow.add_edge(START, 'pm')
        workflow.add_conditional_edges('pm', self.route_pm)
        workflow.add_edge('human', 'pm')
        workflow.add_edge('architect', 'officer')
        workflow.add_conditional_edges('officer', self.route_officer)
        workflow.add_edge('dev', 'reviewer')
        workflow.add_conditional_edges('reviewer', self.route_reviewer)
        workflow.add_conditional_edges('qa', self.route_qa)
        workflow.add_conditional_edges('final-qa', self.route_final_qa)
        workflow.add_edge('reporter', END)
        return workflow.compile(checkpointer=memory, interrupt_before=['human'])

    def route_pm(self, state: dict) -> str:
        if state.get('clarification_question'):
            return 'human'
        return 'architect'

    def route_officer(self, state: dict) -> str:
        if state.get('current_task'):
            return 'dev'
        return 'final-qa'

    def route_reviewer(self, state: dict) -> str:
        feedback = state.get('review_feedback', '').strip().strip('.')
        if feedback.upper() == 'APPROVED':
            return 'qa'
        if state.get('revision_count', 0) >= 3:
            self.logger.warning("Task '%s' reached MAX REVISIONS. Moving on.", state.get('current_task', ''))
            return 'officer'
        return 'dev'

    def route_qa(self, state: dict) -> str:
        results = state.get('test_results', '').strip().strip('.')
        if results.upper() == 'PASSED':
            self.logger.debug("Task '%s' passed all checks!", state.get('current_task', ''))
            return 'officer'
        return 'dev'

    def route_final_qa(self, state: dict) -> str:
        results = state.get('test_results', '').strip().strip('.')
        if results.upper() == 'PASSED':
            return 'reporter'
        return 'dev'

    def queue_manager(self, state: dict) -> dict:
        """Pops the next task and resets task-specific environment"""
        pending = state.get('pending_tasks', [])
        completed = state.get('completed_tasks', [])
        current = state.get('current_task', '')
        if current:
            completed.append(current)
        next_task = pending.pop(0) if pending else ''
        return {
            'pending_tasks': pending,
            'completed_tasks': completed,
            'current_task': next_task,
            'review_feedback': '',
            'test_results': '',
            'revision_count': 0
        }
