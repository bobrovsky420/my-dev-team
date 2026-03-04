from utils import sanitize_for_prompt
from .base import BaseAgent

class CodeJudge(BaseAgent):
    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        drafts = state.get('code_drafts', [])
        drafts_formatted = ""
        for idx, draft in enumerate(drafts):
            draft_idx = f"draft_{idx}"
            safe_draft = sanitize_for_prompt(draft, [draft_idx, 'drafts'])
            drafts_formatted += f"<{draft_idx}>\n{safe_draft}\n</{draft_idx}>\n\n"
        inputs['drafts'] = drafts_formatted
        return inputs

    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        try:
            winner_index = int(parsed_data.get('winner_index', 0))
            winning_code = current_state.get('code_drafts', [])[winner_index]
        except (ValueError, IndexError):
            self.logger.warning("Judge hallucinated; defaulting to draft 0")
            winner_index = 0
            winning_code = current_state.get('code_drafts', [''])[0]
        return {
            'code': winning_code,
            'winner_index': winner_index,
            'task_phase': 'reviewing'
        }
