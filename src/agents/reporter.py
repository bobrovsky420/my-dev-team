from .base import BaseAgent

class Reporter(BaseAgent):
    def process(self, state: dict) -> dict:
        self.logger.info("Generating final report...")
        history_str = '\n\n'.join(state.get('communication_log', []))
        final_report = self.invoke_llm(
            requirements=state.get('requirements'),
            specs=state.get('specs'),
            code=state.get('code'),
            revision_count=state.get('revision_count', 0),
            history=history_str
        )
        return {
            'final_report': final_report
        }
