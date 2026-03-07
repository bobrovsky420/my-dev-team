from utils import sanitize_for_prompt
from .base_agent import BaseAgent

class QAEngineer(BaseAgent):
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

    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        results = parsed_data.get('test_results', '').strip()
        if 'APPROVED' in results.upper() or 'PASSED' in results.upper():
            results = 'APPROVED'
        status = 'APPROVED' if results == 'APPROVED' else 'BUGS FOUND'
        return {
            'test_results': results,
            'communication_log': [f"**[{self.name or self.role}]:** {status}\n{results}"]
        }
