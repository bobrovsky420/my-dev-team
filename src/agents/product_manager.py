from .base_agent import BaseAgent

class ProductManager(BaseAgent):
    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        if 'question' in parsed_data:
            self.logger.info("Need clarification from the user")
            return {
                'clarification_question': parsed_data['question'],
                'specs': '' # Explicitly empty so the router knows we aren't ready for code
            }
        if 'specs' in parsed_data:
            self.logger.info("Generated technical specifications")
            return {
                'specs': parsed_data['specs'],
                'clarification_question': '' # Clear out any old questions
            }
        return {'specs': parsed_data.get('raw_output', '')}
