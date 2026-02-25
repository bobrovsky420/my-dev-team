import re
from .base import BaseAgent

class QAEngineer(BaseAgent):
    def process(self, state: dict) -> dict:
        self.logger.info("Testing code...")
        response = self.invoke_llm({
            'specs': state.get('specs'),
            'code': state.get('code')
        })

        if match := re.search(r'<test_results>(.*?)</test_results>', response, re.DOTALL | re.IGNORECASE):
            results = match.group(1).strip()
        else:
            self.logger.warning("Missing <test_results> tags. Using raw output.")
            results = response.strip()

        return {'test_results': results}
