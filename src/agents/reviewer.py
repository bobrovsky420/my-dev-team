import re
from utils import sanitize_for_prompt
from .base import BaseAgent

class CodeReviewer(BaseAgent):
    def process(self, state: dict) -> dict:
        self.logger.info("Analyzing code...")
        current_task = state.get('current_task', 'Complete project')
        specs = state['specs']
        code = state['code']
        response = self.invoke_llm(
            current_task=sanitize_for_prompt(current_task, ['current_task']),
            specs=sanitize_for_prompt(specs, ['specs']),
            code=sanitize_for_prompt(code, ['code'])
        )
        if match := re.search(r"<feedback>(.*?)</feedback>", response, re.DOTALL | re.IGNORECASE):
            feedback = match.group(1).strip()
        else:
            self.logger.warning("Missing <feedback> tags. Using raw output.")
            feedback = response.strip()
        status = 'APPROVED' if feedback == 'APPROVED' else 'REQUESTED CHANGES'
        return {
            'review_feedback': feedback,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{feedback}"]
        }
