from utils import sanitize_for_prompt
from .base_agent import BaseAgent

class SeniorDeveloper(BaseAgent):
    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        context = ''
        if existing_main := state.get('existing_main_code'):
            context += f"<existing_main_code>\n{sanitize_for_prompt(existing_main, ['existing_main_code', 'context'])}\n</existing_main_code>\n\n"
        if existing_test := state.get('existing_test_code'):
            context += f"<existing_test_code>\n{sanitize_for_prompt(existing_test, ['existing_test_code', 'context'])}\n</existing_test_code>\n\n"
        if main_code := state.get('main_code'):
            context += f"<current_main_draft>\n{sanitize_for_prompt(main_code, ['current_main_draft', 'context'])}\n</current_main_draft>\n\n"
        if test_code := state.get('test_code'):
            context += f"<current_test_draft>\n{sanitize_for_prompt(test_code, ['current_test_draft', 'context'])}\n</current_test_draft>\n\n"
        if feedback := state.get('review_feedback'):
            context += f"<review_feedback>\n{sanitize_for_prompt(feedback, ['review_feedback', 'context'])}\n</review_feedback>\n\n"
        if test_results := state.get('test_results'):
            context += f"<test_results>\n{sanitize_for_prompt(test_results, ['test_results', 'context'])}\n</test_results>\n\n"
        inputs['context'] = context.strip()
        return inputs

    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        main_code = parsed_data.get('main_code', '').strip()
        test_code = parsed_data.get('test_code', '').strip()
        is_revision = bool(current_state.get('main_code'))
        new_revision_count = current_state.get('revision_count', 0) + (1 if is_revision else 0)
        return {
            'main_code': main_code,
            'test_code': test_code,
            'revision_count': new_revision_count,
            'review_feedback': '',
            'test_results': '',
            'communication_log': [f"**[{self.name or self.role}]**: Wrote code draft. (Revision: {new_revision_count})"]
        }
