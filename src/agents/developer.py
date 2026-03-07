from utils import sanitize_for_prompt
from .base_agent import BaseAgent

class SeniorDeveloper(BaseAgent):
    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        workspace_str = ''
        workspace_files = state.get('workspace_files', {})
        if workspace_files:
            for filepath, content in workspace_files.items():
                clean_content = sanitize_for_prompt(content, [filepath, 'workspace'])
                workspace_str += f"--- FILE: {filepath} ---\n{clean_content}\n\n"
        else:
            workspace_str = "No files exist yet. This is the first task. Please create the initial file structure."
        feedback_str = ''
        if review := state.get('review_feedback'):
            feedback_str += f"<review_feedback>\n{sanitize_for_prompt(review, ['review_feedback'])}\n</review_feedback>\n\n"
        if test_res := state.get('test_results'):
            feedback_str += f"<test_results>\n{sanitize_for_prompt(test_res, ['test_results'])}\n</test_results>\n\n"
        if feedback_str:
            workspace_str += f"\n\n### ACTIVE BUG REPORTS TO FIX ###\n{feedback_str}"
        inputs['workspace'] = workspace_str.strip()
        return inputs

    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        workspace_files = current_state.get('workspace_files', {}).copy()
        extracted_files = parsed_data.get('workspace_files', [])
        files_modified = 0
        for filepath, content in extracted_files:
            filepath = filepath.strip()
            workspace_files[filepath] = content.strip()
            files_modified += 1
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
