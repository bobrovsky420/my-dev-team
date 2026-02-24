import logging
from .base import BaseAgent

class QAEngineer(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- QA Engineer testing code ---")
        results = self.invoke_llm({
            'specs': state.get('specs'),
            'code': state.get('code')
        })
        logging.debug("*"*50 + "\n%s\n" + "*"*50, results)
        return {'test_results': results}
