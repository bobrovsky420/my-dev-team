from devteam.utils import is_approved_status
from .base_agent import BaseAgent
from .schemas import CodeReviewerResponse

class CodeReviewer(BaseAgent[CodeReviewerResponse]):
    output_schema = CodeReviewerResponse

    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        workspace_str = ''
        if workspace_files := state.get('workspace_files', {}):
            for filepath, content in workspace_files.items():
                clean_content = self.sanitize_for_prompt(content, [filepath, 'workspace'])
                workspace_str += f"--- FILE: {filepath} ---\n{clean_content}\n\n"
        else:
            workspace_str = "No files exist in the workspace."
        inputs['workspace'] = workspace_str.strip()
        return inputs

    def _update_state(self, parsed_data: CodeReviewerResponse, current_state: dict) -> dict:
        feedback = parsed_data.review_feedback
        if is_approved_status(feedback):
            feedback = 'APPROVED'
        status = 'APPROVED' if feedback == 'APPROVED' else 'REQUESTED CHANGES'
        return {
            'review_feedback': feedback,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{feedback}"]
        }
