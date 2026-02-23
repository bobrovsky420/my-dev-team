from .base import BaseAgent
from langchain_core.prompts import PromptTemplate

class CodeReviewer(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- Code Reviewer analyzing code ---")
        prompt = PromptTemplate.from_template(
            "You are a strict Code Reviewer. Review the following code based on the specs.\n"
            "Specs: {specs}\nCode: {code}\n\n"
            "If the code is perfect, output exactly 'APPROVED'. "
            "Otherwise, provide detailed feedback on what needs to be fixed."
        )
        chain = prompt | self.llm
        feedback = chain.invoke({
            'specs': state.get('specs'),
            'code': state.get('code')
        }).content

        return {'review_feedback': feedback}
