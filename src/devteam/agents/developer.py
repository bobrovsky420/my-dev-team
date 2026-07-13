from typing import override
from devteam.state import ProjectState
from devteam.utils import workspace
from .schemas import DeveloperResponse
from .base_agent import BaseAgent

class SeniorDeveloper(BaseAgent[DeveloperResponse]):
    output_schema = DeveloperResponse

    @override
    def _input_workspace(self, state: ProjectState) -> str:
        return workspace.list_workspace_files(state.workspace_path)

    @override
    def _update_state(self, parsed_data: DeveloperResponse, current_state: ProjectState) -> dict:
        files: dict[str, str] = {f.path: f.content for f in parsed_data.workspace_files}
        files_modified = len(parsed_data.workspace_files)
        current_revision = current_state.task_context.revision_count
        new_drafts = {**current_state.task_context.developer_drafts, self.node_name: files}
        return {
            'task_context': current_state.task_context.model_copy(update={
                'review_feedback': '',
                'test_results': '',
                'developer_drafts': new_drafts,
            }),
            'communication_log': self.communication(f"Wrote/modified {files_modified} file(s)." + (f" (Revision: {current_revision})" if current_revision > 0 else ""))
        }

