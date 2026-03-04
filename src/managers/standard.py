from .base import BaseManager

class StandardManager(BaseManager):
    def __init__(self, developer_name: str):
        super().__init__()
        self.developer = developer_name

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
