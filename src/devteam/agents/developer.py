from devteam.utils import workspace_str_from_files
from .schemas import DeveloperResponse, SubmitCode
from .base_agent import BaseAgent

class SeniorDeveloper(BaseAgent[DeveloperResponse]):
    output_schema = DeveloperResponse
    tools = [SubmitCode]

    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        if workspace_files := state.get('workspace_files', {}):
            workspace_str = workspace_str_from_files(workspace_files)
        else:
            workspace_str = "No files exist yet. This is the first task. Please create the initial file structure."
        inputs['workspace'] = workspace_str
        return inputs

    def _update_state(self, parsed_data: DeveloperResponse, current_state: dict) -> dict:
        workspace_files = current_state.get('workspace_files', {}).copy()
        for file_obj in parsed_data.workspace_files:
            workspace_files[file_obj.path] = file_obj.content
        files_modified = len(parsed_data.workspace_files)
        is_revision = bool(current_state.get('review_feedback') or current_state.get('test_results'))
        new_revision_count = current_state.get('revision_count', 0) + (1 if is_revision else 0)
        return {
            'workspace_files': workspace_files,
            'revision_count': new_revision_count,
            'review_feedback': '',
            'test_results': '',
            'communication_log': [
                f"**[{self.name or self.role}]**: Wrote/modified {files_modified} file(s). (Revision: {new_revision_count})"
            ]
        }
