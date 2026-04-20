from typing import override
from devteam.state import ProjectState
from devteam.utils import sanitizer, workspace
from .schemas import CodeJudgeResponse
from .base_agent import BaseAgent

class CodeJudge(BaseAgent[CodeJudgeResponse]):
    output_schema = CodeJudgeResponse

    @override
    def _build_inputs(self, state: ProjectState) -> dict:
        inputs = super()._build_inputs(state)
        drafts = state.task_context.developer_drafts
        drafts_parts = []
        for idx, (dev_name, files) in enumerate(drafts.items()):
            draft_idx = f"draft_{idx}"
            draft_content = workspace.workspace_str_from_files(files)
            safe_draft = sanitizer.sanitize_for_prompt(draft_content, [draft_idx, 'drafts'])
            drafts_parts.append(f"<{draft_idx}>\n{safe_draft}\n</{draft_idx}>")
        inputs['drafts'] = '\n\n'.join(drafts_parts)
        return inputs

    @override
    def _update_state(self, parsed_data: CodeJudgeResponse, current_state: ProjectState) -> dict:
        draft_items = list(current_state.task_context.developer_drafts.items())
        try:
            winner_name, winning_files = draft_items[parsed_data.winner_index]
        except (IndexError, ValueError):
            self.logger.warning("Judge hallucinated; defaulting to first draft")
            winner_name, winning_files = draft_items[0]
        return {
            'task_context': current_state.task_context.model_copy(update={
                'winner_developer': winner_name,
                'developer_drafts': {winner_name: winning_files},
            }),
            'communication_log': self.communication(f"Selected '{winner_name}' as the winning implementation.")
        }
