from .base_agent import BaseAgent
from .schemas import QAEngineerResponse

class FinalQAEngineer(BaseAgent[QAEngineerResponse]):
    def _update_state(self, parsed_data: QAEngineerResponse, current_state: dict) -> dict:
        results = parsed_data.test_results
        status = 'PASSED' if results == 'PASSED' else 'INTEGRATION BUGS FOUND'
        updates = {
            'test_results': results,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{results}"]
        }
        if status != 'PASSED':
            updates['current_task'] = "FINAL INTEGRATION: Fix the overarching bugs identified in the Final QA test results."
            updates['revision_count'] = 0
        return updates
