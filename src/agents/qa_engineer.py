from .base_agent import BaseAgent

class QAEngineer(BaseAgent):
    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        results = parsed_data.get('test_results') or parsed_data.get('raw_output', '').strip()
        status = 'PASSED' if results == 'PASSED' else 'BUGS FOUND'
        return {
            'test_results': results,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{results}"]
        }
