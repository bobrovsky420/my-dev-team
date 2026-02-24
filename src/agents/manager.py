from langgraph.graph import END
from .base import BaseAgent

class CrewManager(BaseAgent):
    def router(self, state: dict) -> dict:
        print("--- Crew Manager routing workflow ---")
        is_approved = 'APPROVED' in state.get('review_feedback', '')
        is_passed = 'PASSED' in state.get('test_results', '')
        if state.get('clarification_question'):
            next_node = 'human'
        elif state.get('human_answer') and not state.get('specs'):
            next_node = 'pm'
        elif not state.get('specs'):
            next_node = 'pm'
        elif not state.get('code'):
            next_node = 'developer'
        elif state.get('revision_count', 0) > 3:
            print("    -> MAX REVISIONS REACHED. Routing to final report.")
            next_node = 'report'
        elif not state.get('review_feedback'):
            next_node = 'reviewer'
        elif not is_approved:
            next_node = 'developer' # Needs fixes
        elif not state.get('test_results'):
            next_node = 'qa'
        elif not is_passed:
            next_node = 'developer' # Bugs found
        else:
            next_node = 'report'
        print(f"    -> Crew Manager assigns task to: {next_node}")
        return {'next_agent': next_node}

    def process(self, state: dict) -> dict:
        print("--- Crew Manager generating final report ---")
        final_report = self.invoke_llm({
            'requirements': state.get('requirements'),
            'specs': state.get('specs'),
            'code': state.get('code'),
            'revision_count': state.get('revision_count', 0)
        })
        return {
            'final_report': final_report,
            'next_agent': END
        }
