from .base_agent import BaseAgent

class CodeReviewer(BaseAgent):
    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        feedback = parsed_data.get('review_feedback', '').strip()
        if 'APPROVED' in feedback.upper() or 'PASSED' in feedback.upper():
            feedback = 'APPROVED'
        status = 'APPROVED' if feedback == 'APPROVED' else 'REQUESTED CHANGES'
        return {
            'review_feedback': feedback,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{feedback}"]
        }
