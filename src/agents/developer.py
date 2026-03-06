from utils import sanitize_for_prompt
from .base_agent import BaseAgent

class SeniorDeveloper(BaseAgent):
    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        context = ''
        if existing_code := state.get('existing_code'):
            context += f"<existing_code>\n{sanitize_for_prompt(existing_code, ['existing_code', 'context'])}\n</existing_code>\n\n"
        if code := state.get('code'):
            context += f"<current_draft>\n{sanitize_for_prompt(code, ['current_draft', 'context'])}\n</current_draft>\n\n"
        if feedback := state.get('review_feedback'):
            context += f"<review_feedback>\n{sanitize_for_prompt(feedback, ['review_feedback', 'context'])}\n</review_feedback>\n\n"
        if test_results := state.get('test_results'):
            context += f"<test_results>\n{sanitize_for_prompt(test_results, ['test_results', 'context'])}\n</test_results>\n\n"
        inputs['context'] = context.strip()
        return inputs

    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        main_code = parsed_data.get('main_code', '').strip()
        test_code = parsed_data.get('test_code', '').strip()
        final_code = f"### MAIN APP CODE ###\n{main_code}\n\n### TEST CODE ###\n{test_code}"
        is_revision = bool(current_state.get('code'))
        new_revision_count = current_state.get('revision_count', 0) + (1 if is_revision else 0)
        return {
            'code': final_code,
            'revision_count': new_revision_count,
            'review_feedback': '',
            'test_results': '',
            'communication_log': [f"**[{self.name or self.role}]**: Wrote code draft. (Revision: {new_revision_count})"]
        }
