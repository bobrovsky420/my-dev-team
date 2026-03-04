from utils import sanitize_for_prompt
from .base import BaseAgent

class SeniorDeveloper(BaseAgent):
    def _build_inputs(self, state: dict) -> dict:
        inputs = super()._build_inputs(state)
        context = ''
        if code := state.get('code'):
            context += f"<existing_code>\n{sanitize_for_prompt(code, ['existing_code', 'context'])}\n</existing_code>\n"
        if feedback := state.get('review_feedback'):
            context += f"<feedback>\n<review_feedback>\n{sanitize_for_prompt(feedback, ['review_feedback', 'feedback', 'context'])}\n</review_feedback>\n</feedback>\n"
        inputs['context'] = context
        return inputs

    def _update_state(self, parsed_data: dict, current_state: dict) -> dict:
        main_code = parsed_data.get('main_code', '')
        test_code = parsed_data.get('test_code', '')
        final_code = f"### MAIN APP CODE ###\n{main_code}\n\n### TEST CODE ###\n{test_code}"
        if not current_state.get('code'):
            return {'code_drafts': [final_code]}
        return {
            'code': final_code,
            'revision_count': current_state.get('revision_count', 0) + 1,
            'review_feedback': '', # Clear old feedback for the next iteration
            'test_results': ''     # Clear old results for the next iteration
        }
