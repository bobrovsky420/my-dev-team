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

    def _save_code(self, main_code: str, test_code: str, revision_count: int):
        code_file = self.base_dir / f'main_code_v{revision_count}.md'
        code_file.write_text(main_code, encoding='utf-8')
        code_file = self.base_dir / f'test_code_v{revision_count}.md'
        code_file.write_text(test_code, encoding='utf-8')

    def _save_code_review(self, review_feedback: str, revision_count: int):
        feedback_file = self.base_dir / f'feedback_v{revision_count}.md'
        feedback_file.write_text(review_feedback, encoding='utf-8')

    def _save_test_results(self, test_results: str, revision_count: int):
        results_file = self.base_dir / f'test_results_v{revision_count}.md'
        results_file.write_text(test_results, encoding='utf-8')

    def _save_additional_files(self, raw_content: str):
        if not raw_content.strip():
            return
        parts = raw_content.split('FILE: ')
        for part in parts:
            if not part.strip():
                continue
            lines = part.strip().split('\n')
            filename = lines[0].strip()
            content = '\n'.join(lines[1:])
            additional_file = self.base_dir / filename
            additional_file.write_text(content, encoding='utf-8')

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
                    main_code = node_update.get('main_code', '')
                    test_code = node_update.get('test_code', '')
                    revision_count = node_update.get('revision_count', 0)
                    self._save_code(main_code, test_code, revision_count)
                    if extra := node_update.get('additional_files', ''):
                        self._save_additional_files(extra)
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
