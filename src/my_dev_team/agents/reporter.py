from ..utils import sanitize_for_prompt, workspace_str_from_files
from .base_agent import BaseAgent
from .schemas import FinalReportResponse

class Reporter(BaseAgent[FinalReportResponse]):
    output_schema = FinalReportResponse

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
