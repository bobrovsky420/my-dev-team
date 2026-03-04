from utils import sanitize_for_prompt
from .base import BaseAgent

class Reporter(BaseAgent):
    def process(self, state: dict) -> dict:
        self.logger.info("Generating final report...")
        requirements = state['requirements']
        specs = state['specs']
        code = state['code']
        revision_count = state.get('revision_count', 0)
        history_str = '\n\n'.join(state.get('communication_log', []))
        final_report = self.invoke_llm(
            requirements=sanitize_for_prompt(requirements, ['requirements']),
            specs=sanitize_for_prompt(specs, ['specs']),
            code=sanitize_for_prompt(code, ['code']),
            revision_count=revision_count,
            history=sanitize_for_prompt(history_str, ['history'])
        )
        return {
            'final_report': final_report
        }
