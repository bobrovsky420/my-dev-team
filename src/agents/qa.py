from .base import BaseAgent

class QAEngineer(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- QA Engineer testing code ---")
        results = self.invoke_llm({
            'specs': state.get('specs'),
            'code': state.get('code')
        })
        return {'test_results': results}
