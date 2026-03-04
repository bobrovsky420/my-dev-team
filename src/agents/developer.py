import re
from utils import sanitize_for_prompt
from .base import BaseAgent

class SeniorDeveloper(BaseAgent):
    def process(self, state: dict) -> dict:
        self.logger.info("Writing/updating code based on specs...")
        specs = state.get('specs', '')
        current_task = state.get('current_task', 'Complete project')
        existing_code = state.get('code', '') # Only exists AFTER the judge picks a winner
        review_feedback = state.get('review_feedback', '').strip()
        test_results = state.get('test_results', '').strip()

        context = f"<specs>\n{sanitize_for_prompt(specs, ['specs', 'context'])}\n</specs>\n"

        if existing_code:
            context += f"<existing_code>\n{sanitize_for_prompt(existing_code, ['existing_code', 'context'])}\n</existing_code>\n"

        if review_feedback or test_results:
            context += "\n<feedback>\n"
            if review_feedback:
                context += f"\n<review_feedback>\n{sanitize_for_prompt(review_feedback, ['review_feedback', 'feedback', 'context'])}\n</review_feedback>\n"
            if test_results:
                context += f"\n<test_results>\n{sanitize_for_prompt(test_results, ['test_results', 'feedback', 'context'])}\n</test_results>\n"
            context += "</feedback>\n"

        response = self.invoke_llm(
            current_task=current_task,
            context=context
        )

        if main_match := re.search(r"<main_code>(.*?)</main_code>", response, re.DOTALL | re.IGNORECASE):
            main_code = main_match.group(1).strip()
        else:
            self.logger.warning("Missing <main_code> tags. Using raw output.")
            main_code = response.strip()

        if test_match := re.search(r"<test_code>(.*?)</test_code>", response, re.DOTALL | re.IGNORECASE):
            test_code = test_match.group(1).strip()
        else:
            self.logger.warning("Missing <test_code> tags.")
            test_code = ''

        final_code = f"### MAIN APP CODE ###\n{main_code}\n\n### TEST CODE ###\n{test_code}"

        if not existing_code:
            return {
                'code_drafts': [final_code],
                'communication_log': [f"**[{self.name or self.role}]**: Submitted draft."]
            }

        rev_count = state.get('revision_count', 0) + 1
        return {
            'code': final_code,
            'revision_count': rev_count,
            'review_feedback': '', # Clear old feedback for the next iteration
            'test_results': '',    # Clear old results for the next iteration
            'communication_log': [f"**[{self.name or self.role}]**: Submitted Revision {rev_count}."]
        }
