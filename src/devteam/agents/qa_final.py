from devteam.utils.status import is_approved_status
from .schemas import ApproveCode, FinalQAResponse, ReportIssues
from .base_agent import BaseAgent

class FinalQAEngineer(BaseAgent[FinalQAResponse]):
    output_schema = FinalQAResponse
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

    def _map_tool_to_output(self, tool_name: str, tool_args: dict) -> FinalQAResponse:
        if tool_name == 'ApproveCode':
            return FinalQAResponse(evaluation_summary='All checks passed.', test_results='PASSED')
        if tool_name == 'ReportIssues':
            return FinalQAResponse(evaluation_summary='Issues found.', test_results=tool_args['feedback'])
        raise ValueError(f"Unexpected tool call: {tool_name}")

    def _update_state(self, parsed_data: FinalQAResponse, current_state: dict) -> dict:
        results = parsed_data.test_results
        if is_approved_status(results):
            results = 'APPROVED'
        status = 'APPROVED' if results == 'APPROVED' else 'INTEGRATION BUGS FOUND'
        updates = {
            'test_results': results,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{results}"]
        }
        if not is_approved_status(status):
            updates['current_task'] = "FINAL INTEGRATION: Fix the overarching bugs identified in the Final QA test results."
            updates['revision_count'] = 0
        return updates
