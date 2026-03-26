from devteam.utils.status import is_approved_status
from .schemas import ApproveCode, CodeReviewerResponse, ReportIssues
from .base_agent import BaseAgent

class CodeReviewer(BaseAgent[CodeReviewerResponse]):
    output_schema = CodeReviewerResponse
    tools = [ApproveCode, ReportIssues]

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

    def _map_tool_to_output(self, tool_name: str, tool_args: dict) -> CodeReviewerResponse:
        if tool_name == 'ApproveCode':
            return CodeReviewerResponse(review_feedback='APPROVED')
        if tool_name == 'ReportIssues':
            return CodeReviewerResponse(review_feedback=tool_args['feedback'])
        raise ValueError(f"Unexpected tool call: {tool_name}")

    def _update_state(self, parsed_data: CodeReviewerResponse, current_state: dict) -> dict:
        feedback = parsed_data.review_feedback
        if is_approved_status(feedback):
            feedback = 'APPROVED'
        status = 'APPROVED' if feedback == 'APPROVED' else 'REQUESTED CHANGES'
        return {
            'review_feedback': feedback,
            'communication_log': self.communication(f"{status}\n{feedback}")
        }
