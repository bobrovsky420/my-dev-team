from utils import sanitize_for_prompt, is_approved_status
from .base_agent import BaseAgent
from .schemas import FinalQAResponse

class FinalQAEngineer(BaseAgent[FinalQAResponse]):
    output_schema = FinalQAResponse

    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        workspace_str = ''
        if workspace_files := state.get('workspace_files', {}):
            for filepath, content in workspace_files.items():
                clean_content = sanitize_for_prompt(content, [filepath, 'workspace'])
                workspace_str += f"--- FILE: {filepath} ---\n{clean_content}\n\n"
        else:
            workspace_str = "No files exist in the workspace."
        inputs['workspace'] = workspace_str.strip()
        return inputs

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
