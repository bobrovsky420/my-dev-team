from .base import BaseAgent
from langchain_core.prompts import PromptTemplate

class SeniorDeveloper(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- Senior Developer writing/updating code ---")
        specs = state.get('specs', '')
        existing_code = state.get('code', '')
        feedback = state.get('review_feedback', '') + "\n" + state.get('test_results', '')

        context = f"Specs: {specs}\n"
        if existing_code:
            context += f"\nExisting Code:\n{existing_code}\n"
        if feedback.strip():
            context += f"\nFeedback to address:\n{feedback}\n"

        prompt = PromptTemplate.from_template(
            "You are a Senior Python Developer. Write clean, modular, and well-documented Python code "
            "based on the context provided. If there is feedback, fix the existing code.\n\n"
            "Context:\n{context}\n\nCode Implementation:"
        )
        chain = prompt | self.llm
        code = chain.invoke({'context': context}).content

        # Increment revision count if we are updating
        rev_count = state.get('revision_count', 0) + 1 if existing_code else 0

        return {
            'code': code,
            'revision_count': rev_count,
            'review_feedback': '',
            'test_results': ''
        }
