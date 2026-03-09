from .base_agent import BaseAgent

class ProductManager(BaseAgent):
    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        if parsed_data.question:
            self.logger.info("Need clarification from the user")
            return {
                'clarification_question': parsed_data.question,
                'specs': '' # Explicitly empty so the router knows we aren't ready for code
            }
        if parsed_data.specs:
            self.logger.info("Generated technical specifications")
            return {
                'specs': parsed_data.specs,
                'clarification_question': '' # Clear out any old questions
            }
        raise ValueError("Either 'specs' or 'question' must be provided in the response.")
