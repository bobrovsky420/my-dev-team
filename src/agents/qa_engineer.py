from .base_agent import BaseAgent

class QAEngineer(BaseAgent):
    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        results = parsed_data.get('test_results', '').strip()
        if 'APPROVED' in results.upper() or 'PASSED' in results.upper():
            results = 'APPROVED'
        status = 'APPROVED' if results == 'APPROVED' else 'BUGS FOUND'
        return {
            'test_results': results,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{results}"]
        }
