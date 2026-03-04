from langgraph.graph import StateGraph, START, END
from crew.project import ProjectState
from .base import BaseManager

class StandardManager(BaseManager):
    def build_graph(self, agents: dict, developers: dict, memory, human_interrupter):
        workflow = StateGraph(ProjectState)
        workflow.add_node('officer', self.queue_manager)
        workflow.add_node('human', human_interrupter)
        workflow.add_node('pm', agents['pm'].process)
        workflow.add_node('architect', agents['architect'].process)
        workflow.add_node('reviewer', agents['reviewer'].process)
        workflow.add_node('qa', agents['qa'].process)
        workflow.add_node('final-qa', agents['final-qa'].process)
        workflow.add_node('reporter', agents['reporter'].process)
        dev_name = developers.keys()[0]  # Get the first (and only) developer's name
        workflow.add_node(dev_name, developers[dev_name].process)
        workflow.add_conditional_edges(START, self.router)
        workflow.add_conditional_edges('human', self.router)
        workflow.add_conditional_edges('pm', self.router)
        workflow.add_edge('architect', 'officer')
        workflow.add_conditional_edges('officer', self.router)
        workflow.add_edge(dev_name, 'reviewer')
        workflow.add_conditional_edges('reviewer', self.router)
        workflow.add_conditional_edges('qa', self.router)
        workflow.add_conditional_edges('final-qa', self.router)
        workflow.add_edge('reporter', END)
        return workflow.compile(checkpointer=memory, interrupt_before=['human'])

    def router(self, state: dict) -> str:
        self.logger.info("Routing workflow (Standard)...")
        feedback = state.get('review_feedback', '').strip().strip('.')
        results = state.get('test_results', '').strip().strip('.')
        is_approved = (feedback.upper() == 'APPROVED')
        is_passed = (results.upper() == 'PASSED')
        pending_tasks = state.get('pending_tasks', [])
        current_task = state.get('current_task', '')
        completed_tasks = state.get('completed_tasks', [])
        # 1. EARLY INTERRUPTIONS
        if state.get('clarification_question'): return 'human'
        if state.get('human_answer') and not state.get('specs'): return 'pm'
        if not state.get('specs'): return 'pm'
        # 2. SYSTEM ARCHITECT
        if state.get('specs') and not pending_tasks and not current_task and not completed_tasks:
            return 'architect'
        # 3. QUEUE MANAGEMENT
        if not current_task and pending_tasks: return 'officer'
        if not current_task and not pending_tasks: return 'final_qa'
        # 4. SINGLE DEV EXECUTION & BUG FIXING LOOP
        if state.get('revision_count', 0) >= 3:
            self.logger.warning("Task '%s' reached MAX REVISIONS. Moving on.", current_task)
            return 'officer'
        # If this is a brand new task (0 revisions), send directly to dev
        if state.get('revision_count', 0) == 0:
            return self.developer
        # If code exists but hasn't been reviewed/tested
        if not state.get('review_feedback'): return 'reviewer'
        if not is_approved: return self.developer
        if not state.get('test_results'): return 'qa'
        if not is_passed: return self.developer
        # 5. TASK COMPLETION
        self.logger.info("Task '%s' passed all checks!", current_task)
        return 'officer'

    def queue_manager(self, state: dict) -> dict:
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
