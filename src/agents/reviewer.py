import logging
from .base import BaseAgent

class CodeReviewer(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- Code Reviewer analyzing code ---")
        feedback = self.invoke_llm({
            'specs': state.get('specs'),
            'code': state.get('code')
        })
        logging.debug("*"*50 + "\n%s\n" + "*"*50, feedback)
        return {'review_feedback': feedback}
