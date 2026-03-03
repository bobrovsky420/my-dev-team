import logging

class CrewManager:
    name = 'crew-manager'

    def __init__(self, developers: list[str]):
        self.logger = logging.getLogger(self.name )
        self.developers = developers

    def router(self, state: dict) -> str:
        self.logger.info("Routing workflow...")
        feedback = state.get('review_feedback', '').strip().strip('.')
        results = state.get('test_results', '').strip().strip('.')
        is_approved = (feedback.upper() == 'APPROVED')
        is_passed = (results.upper() == 'PASSED')
        pending_tasks = state.get('pending_tasks', [])
        current_task = state.get('current_task', '')
        completed_tasks = state.get('completed_tasks', [])
        winner_idx = state.get('winner_index', 0)
        winning_dev_node = self.developers[winner_idx] if winner_idx < len(self.developers) else self.developers[0]
        # ---------------------------------------------------------
        # 1. EARLY INTERRUPTIONS (Humans & PM)
        # ---------------------------------------------------------
        if state.get('clarification_question'):
            return 'human'
        if state.get('human_answer') and not state.get('specs'):
            return 'pm'
        if not state.get('specs'):
            return 'pm'
        # ---------------------------------------------------------
        # 2. SYSTEM ARCHITECT (Specs exist, but no tasks planned yet)
        # ---------------------------------------------------------
        if state.get('specs') and not pending_tasks and not current_task and not completed_tasks:
            self.logger.info("Specs found. Routing to System Architect for task breakdown.")
            return 'architect'
        # ---------------------------------------------------------
        # 3. QUEUE MANAGEMENT
        # ---------------------------------------------------------
        if not current_task and pending_tasks:
            self.logger.info("Ready for next task. Routing to Project Officer.")
            return 'officer'
        if not current_task and not pending_tasks:
            self.logger.info("All tasks completed! Routing to Final Integration QA.")
            return 'final_qa'
        # ---------------------------------------------------------
        # 4. THE A/B DRAFTING PHASE (Per Task)
        # ---------------------------------------------------------
        if state.get('task_phase', 'drafting') == 'drafting':
            drafts = state.get('code_drafts', [])
            if len(drafts) < len(self.developers):
                next_node = self.developers[len(drafts)]
                self.logger.info(f"Task '{current_task}' | Drafting Phase: Routing to {next_node}")
                return next_node
            else:
                self.logger.info(f"Task '{current_task}' | Drafting Phase: All drafts received. Routing to Judge.")
                return 'judge'
        # ---------------------------------------------------------
        # 5. THE MICRO-QA BUG-FIXING LOOP (Using the Judge's Winner)
        # ---------------------------------------------------------
        if state.get('revision_count', 0) >= 3:
            self.logger.warning(f"Task '{current_task}' reached MAX REVISIONS. Moving to next task.")
            return 'manager_pulls_next_task'
        if not state.get('review_feedback'):
            return 'reviewer'
        if not is_approved:
            self.logger.info(f"Code rejected by Reviewer. Routing fixes back to {winning_dev_node}.")
            return winning_dev_node
        if not state.get('test_results'):
            return 'qa'
        if not is_passed:
            self.logger.info(f"Code failed QA. Routing fixes back to {winning_dev_node}.")
            return winning_dev_node
        # ---------------------------------------------------------
        # 6. TASK COMPLETION
        # ---------------------------------------------------------
        self.logger.info(f"Task '{current_task}' passed all checks! Pulling next task.")
        return 'manager_pulls_next_task'

    def queue_manager(self, state: dict) -> dict:
        """Pops the next task and resets the A/B development environment."""
        pending = state.get('pending_tasks', [])
        completed = state.get('completed_tasks', [])
        current = state.get('current_task', '')
        if current:
            completed.append(current)
        next_task = pending.pop(0) if pending else ''
        if next_task:
            self.logger.info(f"Setting up environment for task: {next_task}")
        else:
            self.logger.info("Task queue is empty.")
        return {
            'pending_tasks': pending,
            'completed_tasks': completed,
            'current_task': next_task,
            # Wipe the drafting/QA slate clean for the new task
            'code_drafts': [],
            'task_phase': 'drafting',
            'winner_index': 0,
            'review_feedback': '',
            'test_results': '',
            'revision_count': 0
        }
