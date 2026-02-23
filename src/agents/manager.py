from langgraph.graph import END
from .base import BaseAgent

class CrewManager(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- Crew Manager routing workflow ---")
        if not state.get('specs'):
            next_node = 'pm'
        elif not state.get('code'):
            next_node = 'developer'
        elif state.get('revision_count', 0) > 3:
            print("    -> MAX REVISIONS REACHED. Forcing finish.")
            next_node = END
        elif not state.get('review_feedback'):
            next_node = 'reviewer'
        elif 'APPROVED' not in state.get('review_feedback', ''):
            next_node = 'developer' # Needs fixes
        elif not state.get('test_results'):
            next_node = 'qa'
        elif 'PASSED' not in state.get('test_results', ''):
            next_node = 'developer' # Bugs found
        else:
            next_node = END
        print(f"    -> Crew Manager assigns task to: {next_node}")
        return {'next_agent': next_node}
