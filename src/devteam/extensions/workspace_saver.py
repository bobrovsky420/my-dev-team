from pathlib import Path
from ..utils import task_to_markdown
from .base_extension import CrewExtension

class WorkspaceSaver(CrewExtension):
    base_dir: Path

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def on_start(self, thread_id: str, initial_state: dict):
        self.base_dir = self._get_target_dir('pm', initial_state)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if requirements := initial_state.get('requirements'):
            self._save_requirements(requirements)

    def _get_target_dir(self, node_name: str, full_state: dict) -> Path:
        if node_name in ['pm', 'architect']:
            return self.workspace_dir / '00_planning'
        if node_name in ['reporter', 'final_qa']:
            return self.workspace_dir / '90_integration'
        if node_name == 'qa' and full_state.get('current_task') == 'ALL_DONE':
            return self.workspace_dir / '90_integration'
        if task_idx := full_state.get('current_task_index', 0):
            return self.workspace_dir / f'{task_idx:02d}_task'
        return self.workspace_dir / '00_planning'

    def _save_requirements(self, requirements: str):
        requirements_file = self.base_dir / 'requirements.md'
        requirements_file.write_text(requirements, encoding='utf-8')

    def _save_specs(self, specs: str):
        specs_file = self.base_dir / 'specs.md'
        specs_file.write_text(specs, encoding='utf-8')

    def _save_tasks(self, tasks: list):
        tasks_file = self.base_dir / 'tasks.md'
        content = ["# System Execution Plan\n"]
        for idx, task in enumerate(tasks, start=1):
            content.append(task_to_markdown(task, idx))
        tasks_file.write_text('\n'.join(content), encoding='utf-8')

    def _save_workspace(self, workspace_files: dict, current_rev: int):
        if not workspace_files:
            return
        revision_dir = f'rev_{current_rev}'
        for filepath, content in workspace_files.items():
            full_file_path = self.base_dir / revision_dir / filepath
            full_file_path.parent.mkdir(parents=True, exist_ok=True)
            full_file_path.write_text(content, encoding='utf-8')

    def _save_code_review(self, review_feedback: str, current_rev: int):
        feedback_file = self.base_dir / f'feedback_v{current_rev}.md'
        feedback_file.write_text(review_feedback, encoding='utf-8')

    def _save_test_results(self, test_results: str, current_rev: int):
        results_file = self.base_dir / f'test_results_v{current_rev}.md'
        results_file.write_text(test_results, encoding='utf-8')

    def _save_final_report(self, report: str):
        report_file = self.base_dir / 'final_report.md'
        report_file.write_text(report, encoding='utf-8')

    def on_step(self, thread_id: str, *, state_update: dict, full_state: dict):
        for node_name, node_update in state_update.items():
            self.base_dir = self._get_target_dir(node_name, full_state)
            self.base_dir.mkdir(parents=True, exist_ok=True)
            match node_name:
                case 'pm':
                    if specs := node_update.get('specs', ''):
                        self._save_specs(specs)
                case 'architect':
                    if pending := node_update.get('pending_tasks', []):
                        self._save_tasks(pending)
                case 'developer':
                    workspace_files = node_update.get('workspace_files', {})
                    current_rev = node_update.get('revision_count', 0)
                    self._save_workspace(workspace_files, current_rev)
                case 'reviewer':
                    if review_feedback := node_update.get('review_feedback', ''):
                        current_rev = node_update.get('revision_count', 0)
                        self._save_code_review(review_feedback, current_rev)
                case 'qa':
                    if test_results := node_update.get('test_results', ''):
                        current_rev = node_update.get('revision_count', 0)
                        self._save_test_results(test_results, current_rev)
                case 'reporter':
                    if final_report := node_update.get('final_report', ''):
                        self._save_final_report(final_report)
