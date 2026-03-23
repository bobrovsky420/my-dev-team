from .schemas import CodeJudgeResponse, SubmitWinner
from .base_agent import BaseAgent


class CodeJudge(BaseAgent[CodeJudgeResponse]):
    output_schema = CodeJudgeResponse
    tools = [SubmitWinner]

    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        drafts = state.get('code_drafts', [])
        drafts_formatted = ""
        for idx, draft in enumerate(drafts):
            draft_idx = f"draft_{idx}"
            safe_draft = self.sanitize_for_prompt(draft, [draft_idx, 'drafts'])
            drafts_formatted += f"<{draft_idx}>\n{safe_draft}\n</{draft_idx}>\n\n"
        inputs['drafts'] = drafts_formatted
        return inputs

    def _map_tool_to_output(self, tool_name: str, tool_args: dict) -> CodeJudgeResponse:
        if tool_name == 'SubmitWinner':
            return CodeJudgeResponse(winner_index=tool_args['winner_index'])
        raise ValueError(f"Unexpected tool call: {tool_name}")

    def _update_state(self, parsed_data: CodeJudgeResponse, current_state: dict) -> dict:
        try:
            winner_index = parsed_data.winner_index
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
