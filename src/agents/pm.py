from .base import BaseAgent
from langchain_core.prompts import PromptTemplate

class ProductManager(BaseAgent):
    def process(self, state: dict) -> dict:
        print("--- Product Manager working on Specs ---")
        prompt = PromptTemplate.from_template(
            "You are an expert Product Manager. Based on the following stakeholder requirements, "
            "write a detailed, structured technical specification for the engineering team.\n\n"
            "Requirements: {requirements}\n\nTechnical Specifications:"
        )
        chain = prompt | self.llm
        specs = chain.invoke({'requirements': state.get('requirements')}).content
        return {'specs': specs}
