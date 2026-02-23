from .base import BaseAgent

class CodeReviewer(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- Code Reviewer analyzing code ---")
        chain = self.prompt | self.llm
        feedback = chain.invoke({
            'specs': state.get('specs'),
            'code': state.get('code')
        }).content
        return {'review_feedback': feedback}
