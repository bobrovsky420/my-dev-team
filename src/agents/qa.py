import re
from utils import sanitize_for_prompt
from .base import BaseAgent

class QAEngineer(BaseAgent):
    def process(self, state: dict) -> dict:
        self.logger.info("Testing code...")
        current_task = state.get('current_task', 'Complete project')
        specs = state['specs']
        code = state['code']
        response = self.invoke_llm(
            current_task=sanitize_for_prompt(current_task, ['current_task']),
            specs=sanitize_for_prompt(specs, ['specs']),
            code=sanitize_for_prompt(code, ['code'])
        )
        if match := re.search(r"<test_results>(.*?)</test_results>", response, re.DOTALL | re.IGNORECASE):
            results = match.group(1).strip()
        else:
            self.logger.warning("Missing <test_results> tags. Using raw output.")
            results = response.strip()
        status = 'PASSED' if results == 'PASSED' else 'BUGS FOUND'
        return {
            'test_results': results,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{results}"]
        }
