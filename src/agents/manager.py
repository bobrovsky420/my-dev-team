from langgraph.graph import END
from .base import BaseAgent

class CrewManager(BaseAgent):
    def router(self, state: dict) -> dict:
        self.logger.info("Routing workflow...")
        feedback = state.get('review_feedback', '').strip().upper().strip('.')
        results = state.get('test_results', '').strip().upper().strip('.')
        is_approved = (feedback == 'APPROVED')
        is_passed = (results == 'PASSED')
        if state.get('clarification_question'):
            next_node = 'human'
        elif state.get('human_answer') and not state.get('specs'):
            next_node = 'pm'
        elif not state.get('specs'):
            next_node = 'pm'
        elif not state.get('code'):
            next_node = 'developer'
        elif state.get('revision_count', 0) >= 3:
            self.logger.warning("MAX REVISIONS REACHED. Forcing finish.")
            next_node = 'report'
        elif not state.get('review_feedback'):
            next_node = 'reviewer'
        elif not is_approved:
            self.logger.info("Code rejected by Reviewer. Routing back to Developer.")
            next_node = 'developer'
        elif not state.get('test_results'):
            next_node = 'qa'
        elif not is_passed:
            self.logger.info("Code failed QA. Routing back to Developer.")
            next_node = 'developer'
        else:
            self.logger.info("Code passed all checks! Routing to Final Report.")
            next_node = 'report'
        self.logger.info("Assigns task to: %s", next_node)
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
