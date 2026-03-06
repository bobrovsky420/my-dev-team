import os
from pathlib import Path
from .base_extension import CrewExtension

class WorkspaceSaver(CrewExtension):
    root_dir = Path('workspaces')

    def on_start(self, thread_id: str, initial_state: dict):
        base_dir = self.root_dir / thread_id
        os.makedirs(base_dir, exist_ok=True)
        requirements_file = base_dir / 'requirements.md'
        requirements_file.write_text(initial_state.get('requirements', ''), encoding='utf-8')

    def _save_specs(self, base_dir: Path, specs: str):
        specs_file = base_dir / 'specs.md'
        specs_file.write_text(specs, encoding='utf-8')

    def _save_tasks(self, base_dir: Path, tasks: list[str]):
        tasks_file = base_dir / 'tasks.md'
        content = ["# System Execution Plan\n"]
        for i, task in enumerate(tasks, start=1):
            ticket_markdown = (
                f"## Task {i}\n"
                f"{task.strip()}\n\n"
                f"---\n"
            )
            content.append(ticket_markdown)
        tasks_file.write_text("\n".join(content), encoding='utf-8')

    def _save_code(self, base_dir: Path, code: str, revision_count: int):
        code_file = base_dir / f'code_v{revision_count}.md'
        code_file.write_text(code, encoding='utf-8')

    def _save_code_review(self, base_dir: Path, review_feedback: str, revision_count: int):
        feedback_file = base_dir / f'feedback_v{revision_count}.md'
        feedback_file.write_text(review_feedback, encoding='utf-8')

    def _save_test_results(self, base_dir: Path, test_results: str, revision_count: int):
        results_file = base_dir / f'test_results_v{revision_count}.md'
        results_file.write_text(test_results, encoding='utf-8')

    def _save_final_report(self, base_dir: Path, report: str):
        report_file = base_dir / 'final_report.md'
        report_file.write_text(report, encoding='utf-8')

    def on_step(self, thread_id: str, *, state_update: dict, full_state: dict):
        base_dir = self.root_dir / thread_id
        for node_name, node_update in state_update.items():
            match node_name:
                case 'pm':
                    if specs := full_state.get('specs', ''):
                        self._save_specs(base_dir, specs)
                case 'architect':
                    if pending := full_state.get('pending_tasks', []):
                        self._save_tasks(base_dir, pending)
                case 'developer':
                    if code := full_state.get('code', ''):
                        self._save_code(base_dir, code, state_update.get('revision_count', 0))
                case 'reviewer':
                    if review_feedback := full_state.get('review_feedback', ''):
                        self._save_code_review(base_dir, review_feedback, full_state.get('revision_count', 0))
                case 'qa':
                    if test_results := full_state.get('test_results', ''):
                        self._save_test_results(base_dir, test_results, full_state.get('revision_count', 0))
                case 'reporter':
                    if final_report := full_state.get('final_report'):
                        self._save_final_report(base_dir, final_report)
