from .base import BaseAgent

class QAEngineer(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- QA Engineer testing code ---")
        chain = self.prompt | self.llm
        results = chain.invoke({
            'specs': state.get('specs'),
            'code': state.get('code')
        }).content
        return {'test_results': results}
