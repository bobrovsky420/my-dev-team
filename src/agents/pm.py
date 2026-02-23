import re
from .base import BaseAgent

class ProductManager(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- Product Manager working on Specs ---")
        chain = self.prompt | self.llm
        specs = chain.invoke({'requirements': state.get('requirements')}).content
        return {'specs': specs}

    def process(self, state: dict) -> dict:
        print("--- Product Manager evaluating requirements ---")

        requirements = state.get('requirements', '')
        human_answer = state.get('human_answer', '')

        chain = self.prompt | self.llm
        response = chain.invoke({
            'requirements': requirements,
            'human_answer': human_answer
        }).content

        if question_match := re.search(r'<question>(.*?)</question>', response, re.DOTALL | re.IGNORECASE):
            question = question_match.group(1).strip()
            print("    -> PM needs clarification from the user.")
            return {
                'clarification_question': question,
                'specs': '' # Explicitly empty so the router knows we aren't ready for code
            }
        elif specs_match := re.search(r'<specs>(.*?)</specs>', response, re.DOTALL | re.IGNORECASE):
            specs = specs_match.group(1).strip()
            print("    -> PM generated technical specifications.")
            return {
                'specs': specs,
                'clarification_question': '' # Clear out any old questions
            }
        else:
            # Fallback: If the local model hallucinates and forgets the XML tags,
            # we gracefully assume the entire response is the specification.
            print("    -> [Warning] PM forgot XML tags. Treating raw output as specs.")
            return {
                'specs': response.strip(),
                'clarification_question': ''
            }
