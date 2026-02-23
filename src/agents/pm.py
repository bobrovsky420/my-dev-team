from .base import BaseAgent

class ProductManager(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- Product Manager working on Specs ---")
        chain = self.prompt | self.llm
        specs = chain.invoke({'requirements': state.get('requirements')}).content
        return {'specs': specs}
