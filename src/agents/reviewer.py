import re

from .base import BaseAgent

class CodeReviewer(BaseAgent):
    def process(self, state: dict) -> dict:
        self.logger.info("Analyzing code...")
        current_task = state.get('current_task', 'Complete project')
        response = self.invoke_llm(
            current_task=current_task,
            specs=state.get('specs'),
            code=state.get('code')
        )
        if match := re.search(r'<feedback>(.*?)</feedback>', response, re.DOTALL | re.IGNORECASE):
            feedback = match.group(1).strip()
        else:
            self.logger.warning("Missing <feedback> tags. Using raw output.")
            feedback = response.strip()
        status = 'APPROVED' if feedback == 'APPROVED' else 'REQUESTED CHANGES'
        return {
            'review_feedback': feedback,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{feedback}"]
        }
