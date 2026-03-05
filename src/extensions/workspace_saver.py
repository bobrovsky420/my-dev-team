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
        content = "# System Execution Plan\n\n" + "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
        tasks_file.write_text(content, encoding='utf-8')

    def _save_code(self, base_dir: Path, code: str):
        code_file = base_dir / 'code.md'
        code_file.write_text(code, encoding='utf-8')

    def _save_final_report(self, base_dir: Path, report: str):
        report_file = base_dir / 'final_report.md'
        report_file.write_text(report, encoding='utf-8')

    def on_step(self, thread_id: str, current_state: dict):
        base_dir = self.root_dir / thread_id

        pending = current_state.get('pending_tasks', [])
        current = current_state.get('current_task', '')
        completed = current_state.get('completed_tasks', [])
        rev = current_state.get('revision_count', 0)

        if current_state.get('specs'):
            self._save_specs(base_dir, current_state['specs'])

        if pending and not current and not completed:
            self._save_tasks(base_dir, pending)

        if current_state.get('code'):
            self._save_code(base_dir, current_state['code'])

        if current_state.get('final_report'):
            self._save_final_report(base_dir, current_state['final_report'])

        if current:
            task_num = len(completed) + 1
            task_dir = base_dir / f'task_{task_num:02d}'
            drafts_dir = task_dir / 'drafts'
            revisions_dir = task_dir / 'revisions'
            os.makedirs(drafts_dir, exist_ok=True)
            os.makedirs(revisions_dir, exist_ok=True)
            task_file = task_dir / 'task_description.md'
            task_file.write_text(current, encoding='utf-8')
            if current_state.get('code_drafts'):
                for idx, draft in enumerate(current_state['code_drafts']):
                    draft_file = drafts_dir / f'draft_{idx}.md'
                    draft_file.write_text(draft, encoding='utf-8')
            if current_state.get('review_feedback'):
                feedback_file = revisions_dir / f'feedback_v{rev}.md'
                feedback_file.write_text(current_state['review_feedback'], encoding='utf-8')
            if current_state.get('test_results'):
                tests_file = revisions_dir / f'tests_v{rev}.md'
                tests_file.write_text(current_state['test_results'], encoding='utf-8')
