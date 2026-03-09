from utils import sanitize_for_prompt, workspace_str_from_files
from .base_agent import BaseAgent

class Reporter(BaseAgent):
    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        if workspace_files := state.get('workspace_files', {}):
            workspace_str = workspace_str_from_files(workspace_files)
        else:
            workspace_str = "No files were generated."
        inputs['workspace'] = workspace_str
        communication_log = state.get('communication_log', [])
        history_str = '\n\n'.join(communication_log)
        inputs['history'] = sanitize_for_prompt(history_str, ['history'])
        return inputs

    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        report = parsed_data.get('raw_output', '').strip()
        return {
            'final_report': report
        }
