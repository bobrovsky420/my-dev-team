from langgraph.graph import END
from .base import BaseAgent

class CrewManager(BaseAgent):
    developers: list[str]

    def router(self, state: dict) -> dict:
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
            next_node = 'human'
        elif state.get('human_answer') and not state.get('specs'):
            next_node = 'pm'
        elif not state.get('specs'):
            next_node = 'pm'
        # ---------------------------------------------------------
        # 2. SYSTEM ARCHITECT (Specs exist, but no tasks planned yet)
        # ---------------------------------------------------------
        elif state.get('specs') and not pending_tasks and not current_task and not completed_tasks:
            self.logger.info("Specs found. Routing to System Architect for task breakdown.")
            next_node = 'architect'
        # ---------------------------------------------------------
        # 3. QUEUE MANAGEMENT
        # ---------------------------------------------------------
        elif not current_task and pending_tasks:
            self.logger.info("Ready for next task. Routing to Project Officer.")
            next_node = 'officer'
        elif not current_task and not pending_tasks:
            self.logger.info("All tasks completed! Routing to Final Integration QA.")
            next_node = 'final_qa'
        # ---------------------------------------------------------
        # 4. THE A/B DRAFTING PHASE (Per Task)
        # ---------------------------------------------------------
        elif state.get('task_phase', 'drafting') == 'drafting':
            drafts = state.get('code_drafts', [])
            if len(drafts) < len(self.developers):
                next_node = self.developers[len(drafts)]
                self.logger.info(f"Task '{current_task}' | Drafting Phase: Routing to {next_node}")
            else:
                self.logger.info(f"Task '{current_task}' | Drafting Phase: All drafts received. Routing to Judge.")
                next_node = 'judge'
        # ---------------------------------------------------------
        # 5. THE MICRO-QA BUG-FIXING LOOP (Using the Judge's Winner)
        # ---------------------------------------------------------
        elif state.get('revision_count', 0) >= 3:
            self.logger.warning(f"Task '{current_task}' reached MAX REVISIONS. Moving to next task.")
            next_node = 'manager_pulls_next_task'
        elif not state.get('review_feedback'):
            next_node = 'reviewer'
        elif not is_approved:
            self.logger.info(f"Code rejected by Reviewer. Routing fixes back to {winning_dev_node}.")
            next_node = winning_dev_node
        elif not state.get('test_results'):
            next_node = 'qa'
        elif not is_passed:
            self.logger.info(f"Code failed QA. Routing fixes back to {winning_dev_node}.")
            next_node = winning_dev_node
        # ---------------------------------------------------------
        # 6. TASK COMPLETION
        # ---------------------------------------------------------
        else:
            self.logger.info(f"Task '{current_task}' passed all checks! Pulling next task.")
            next_node = 'manager_pulls_next_task'
        self.logger.info(f"Assigned next node: {next_node}")
        return {'next_agent': next_node}

    """
    def router(self, state: dict) -> dict:
        self.logger.info("Routing workflow...")
        feedback = state.get('review_feedback', '').strip().strip('.')
        results = state.get('test_results', '').strip().strip('.')
        is_approved = (feedback.upper() == 'APPROVED')
        is_passed = (results.upper() == 'PASSED')
        self.logger.debug("Review Feedback: %s | Test Results: %s", feedback, results)
        self.logger.debug("Is Approved: %s | Is Passed: %s", is_approved, is_passed)
        winner_idx = state.get('winner_index', 0)
        winning_dev_node = self.developers[winner_idx] if winner_idx < len(self.developers) else self.developers[0]
        if state.get('clarification_question'):
            next_node = 'human'
        elif state.get('human_answer') and not state.get('specs'):
            next_node = 'pm'
        elif not state.get('specs'):
            next_node = 'pm'
        elif not state.get('code'):
            drafts = state.get('code_drafts', [])
            if len(drafts) < len(self.developers):
                next_node = self.developers[len(drafts)]
            else:
                next_node = 'judge' # Everyone submitted a draft, time to judge!
        elif state.get('revision_count', 0) >= 3:
            self.logger.warning("MAX REVISIONS REACHED. Forcing finish.")
            next_node = 'report'
        elif not state.get('review_feedback'):
            next_node = 'reviewer'
        elif not is_approved:
            self.logger.info(f"Code rejected by Reviewer. Routing code fixes to {winning_dev_node}")
            next_node = winning_dev_node
        elif not state.get('test_results'):
            next_node = 'qa'
        elif not is_passed:
            self.logger.info(f"Code failed QA. Routing code fixes to {winning_dev_node}")
            next_node = winning_dev_node
        else:
            self.logger.info("Code passed all checks! Routing to Final Report.")
            next_node = 'report'
        self.logger.info(f"Assigns task to: {next_node}")
        return {'next_agent': next_node}
    """

    def process(self, state: dict) -> dict:
        self.logger.info("Generating final report...")
        history_str = '\n\n'.join(state.get('communication_log', []))
        final_report = self.invoke_llm(
            requirements=state.get('requirements'),
            specs=state.get('specs'),
            code=state.get('code'),
            revision_count=state.get('revision_count', 0),
            history=history_str
        )
        return {
            'final_report': final_report,
            'next_agent': END
        }
