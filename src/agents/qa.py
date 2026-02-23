from .base import BaseAgent
from langchain_core.prompts import PromptTemplate

class QAEngineer(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- QA Engineer testing code ---")
        prompt = PromptTemplate.from_template(
            "You are a QA Engineer. Evaluate the following code against the specs.\n"
            "Specs: {specs}\nCode: {code}\n\n"
            "Simulate running tests. If the logic passes all edge cases, output exactly 'PASSED'. "
            "Otherwise, provide bug reports and failed test cases."
        )
        chain = prompt | self.llm
        results = chain.invoke({
            'specs': state.get('specs'),
            'code': state.get('code')
        }).content

        return {'test_results': results}
