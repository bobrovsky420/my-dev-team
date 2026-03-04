import re
from utils import sanitize_for_prompt
from .base import BaseAgent

class CodeJudge(BaseAgent):
    def process(self, state: dict) -> dict:
        specs = state.get('specs', '')
        current_task = state.get('current_task', 'Complete project')
        drafts = state.get('code_drafts', [])
        self.logger.info(f"Evaluating {len(drafts)} drafts for task: {current_task}...")
        if not drafts:
            self.logger.error("Judge called but no drafts exist!")
            return {'task_phase': 'reviewing'}
        drafts_formatted = ""
        for idx, draft in enumerate(drafts):
            draft_idx = f"draft_{idx}"
            drafts_formatted += f"<{draft_idx}>\n{sanitize_for_prompt(draft, [draft_idx, 'drafts'])}\n</{draft_idx}>\n\n"
        response = self.invoke_llm(
            specs=sanitize_for_prompt(specs, ['specs']),
            current_task=sanitize_for_prompt(current_task, ['current_task']),
            drafts=drafts_formatted
        )
        match = re.search(r"<winner>(\d+)</winner>", response, re.IGNORECASE)
        try:
            winner_idx = int(match.group(1).strip())
            winning_code = drafts[winner_idx]
        except (AttributeError, ValueError, IndexError):
            self.logger.warning("Judge hallucinated the winner index. Defaulting to Draft 0.")
            winner_idx = 0
            winning_code = drafts[0]
        return {
            'code': winning_code,
            'winner_index': winner_idx,
            'task_phase': 'reviewing',
            'communication_log': [
                f"Evaluated {len(drafts)} drafts for task '{current_task}'. "
                f"Selected Draft {winner_idx} as the superior architecture."
                f"\n\nReasoning: {response}"
            ]
        }
