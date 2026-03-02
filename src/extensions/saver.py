import os
from pathlib import Path
from .extension import CrewExtension

class WorkspaceSaver(CrewExtension):
    root_dir = Path('workspaces')

    def on_start(self, thread_id: str, initial_state: dict):
        base_dir = self.root_dir / thread_id
        os.makedirs(base_dir, exist_ok=True)
        requirements_file = base_dir / 'requirements.txt'
        requirements_file.write_text(initial_state.get('requirements', ''), encoding='utf-8')

    def _save_specs(self, base_dir: Path, specs: str):
        specs_file = base_dir / 'specs.md'
        specs_file.write_text(specs, encoding='utf-8')

    def _save_tasks(self, base_dir: Path, tasks: list[str]):
        tasks_file = base_dir / 'tasks.md'
        tasks_file.write_text('\n'.join(tasks), encoding='utf-8')

    def on_step(self, thread_id: str, current_state: dict):
        base_dir = self.root_dir / thread_id
        drafts_dir = base_dir / 'drafts'
        revisions_dir = base_dir / 'revisions'
        os.makedirs(drafts_dir, exist_ok=True)
        os.makedirs(revisions_dir, exist_ok=True)
        rev = current_state.get('revision_count', 0)
        if 'specs' in current_state and current_state['specs']:
            self._save_specs(base_dir, current_state['specs'])
        if 'pending_tasks' in current_state and current_state['pending_tasks']:
            self._save_tasks(base_dir, current_state['pending_tasks'])
        if 'code_drafts' in current_state:
            drafts = current_state.get('code_drafts', [])
            draft_idx = len(drafts) - 1
            if draft_idx >= 0:
                draft_file = drafts_dir / f'draft_{draft_idx}.md'
                draft_file.write_text(drafts[draft_idx], encoding='utf-8')
        if 'code' in current_state and current_state['code']:
            code_file = base_dir / 'code.md'
            code_file.write_text(current_state['code'], encoding='utf-8')
        if 'review_feedback' in current_state and current_state['review_feedback']:
            feedback_file = revisions_dir / f'feedback_v{rev}.md'
            feedback_file.write_text(current_state['review_feedback'], encoding='utf-8')
        if 'test_results' in current_state and current_state['test_results']:
            tests_file = revisions_dir / f'tests_v{rev}.md'
            tests_file.write_text(current_state['test_results'], encoding='utf-8')
        if 'final_report' in current_state and current_state['final_report']:
            report_file = base_dir / 'final_report.md'
            report_file.write_text(current_state['final_report'], encoding='utf-8')
