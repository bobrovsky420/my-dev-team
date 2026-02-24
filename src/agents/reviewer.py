from .base import BaseAgent

class CodeReviewer(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- Code Reviewer analyzing code ---")
        feedback = self.invoke_llm({
            'specs': state.get('specs'),
            'code': state.get('code')
        })
        return {'review_feedback': feedback}
