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

    def process(self, state: dict) -> dict:
        self.logger.info("Generating final report...")
        history_str = '\n\n'.join(state.get('communication_log', []))
        final_report = self.invoke_llm({
            'requirements': state.get('requirements'),
            'specs': state.get('specs'),
            'code': state.get('code'),
            'revision_count': state.get('revision_count', 0),
            'history': history_str
        })
        return {
            'final_report': final_report,
            'next_agent': END
        }
