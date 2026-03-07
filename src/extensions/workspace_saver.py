import os
from pathlib import Path
from .base_extension import CrewExtension

class WorkspaceSaver(CrewExtension):
    base_dir: Path

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        os.makedirs(self.workspace_dir, exist_ok=True)

    def on_start(self, thread_id: str, initial_state: dict):
        os.makedirs(self.workspace_dir, exist_ok=True)
        if thread_id.endswith('_plan'):
            folder_name = '00_planning'
        elif '_task_' in thread_id:
            task_num = thread_id.split('_task_')[-1]
            folder_name = f'{task_num.zfill(2)}_task'
        elif thread_id.endswith('_integration'):
            folder_name = '90_integration'
        else:
            folder_name = 'misc'
        self.base_dir = self.workspace_dir / folder_name
        os.makedirs(self.base_dir, exist_ok=True)
        is_planning_phase = 'requirements' in initial_state and 'specs' not in initial_state
        if is_planning_phase:
            self._save_requirements(initial_state['requirements'])

    def _save_requirements(self, requirements: str):
        requirements_file = self.base_dir / 'requirements.md'
        requirements_file.write_text(requirements, encoding='utf-8')

    def _save_specs(self, specs: str):
        specs_file = self.base_dir / 'specs.md'
        specs_file.write_text(specs, encoding='utf-8')

    def _save_tasks(self, tasks: list[str]):
        tasks_file = self.base_dir / 'tasks.md'
        content = ["# System Execution Plan\n"]
        for i, task in enumerate(tasks, start=1):
            ticket_markdown = (
                f"## Task {i}\n"
                f"{task.strip()}\n\n"
                f"---\n"
            )
            content.append(ticket_markdown)
        tasks_file.write_text("\n".join(content), encoding='utf-8')

    def _save_workspace(self, revision_dir: str, workspace_files: dict):
        if not workspace_files:
            return
        for filepath, content in workspace_files.items():
            full_file_path = self.base_dir / revision_dir / filepath
            full_file_path.parent.mkdir(parents=True, exist_ok=True)
            full_file_path.write_text(content, encoding='utf-8')

    def _save_code_review(self, review_feedback: str, revision_count: int):
        feedback_file = self.base_dir / f'feedback_v{revision_count}.md'
        feedback_file.write_text(review_feedback, encoding='utf-8')

    def _save_test_results(self, test_results: str, revision_count: int):
        results_file = self.base_dir / f'test_results_v{revision_count}.md'
        results_file.write_text(test_results, encoding='utf-8')

    def _save_final_report(self, report: str):
        report_file = self.base_dir / 'final_report.md'
        report_file.write_text(report, encoding='utf-8')

    def on_step(self, thread_id: str, *, state_update: dict, full_state: dict):
        for node_name, node_update in state_update.items():
            match node_name:
                case 'pm':
                    if specs := node_update.get('specs', ''):
                        self._save_specs(specs)
                case 'architect':
                    if pending := node_update.get('pending_tasks', []):
                        self._save_tasks(pending)
                case 'developer':
                    workspace_files = node_update.get('workspace_files', {})
                    revision_count = full_state.get('revision_count', 0)
                    revision_dir = f'rev_{revision_count}'
                    self._save_workspace(revision_dir, workspace_files)
                case 'reviewer':
                    if review_feedback := node_update.get('review_feedback', ''):
                        current_rev = full_state.get('revision_count', 0)
                        self._save_code_review(review_feedback, current_rev)
                case 'qa':
                    if test_results := node_update.get('test_results', ''):
                        current_rev = full_state.get('revision_count', 0)
                        self._save_test_results(test_results, current_rev)
                case 'reporter':
                    if final_report := node_update.get('final_report', ''):
                        self._save_final_report(final_report)
