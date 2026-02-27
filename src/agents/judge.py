import re
from .base import BaseAgent

class CodeJudge(BaseAgent):
    def process(self, state: dict) -> dict:
        self.logger.info("Evaluating all drafts...")
        drafts = state.get('code_drafts', [])
        drafts_context = ''
        for index, draft in enumerate(drafts):
            drafts_context += f'\n<draft_{index}>\n{draft}\n</draft_{index}>\n'
        response = self.invoke_llm({
            'specs': state.get('specs'),
            'drafts': drafts_context
        })
        match = re.search(r'<winner>(\d+)</winner>', response, re.IGNORECASE)
        try:
            winner_idx = int(match.group(1).strip())
            winning_code = drafts[winner_idx]
        except (AttributeError, ValueError, IndexError):
            self.logger.warning("Judge hallucinated the winner index. Defaulting to Draft 0.")
            winner_idx = 0
            winning_code = drafts[0]
        return {
            'code': winning_code,
            'winner_index': winner_idx,
            'communication_log': [f"**[{self.name or self.role}]**: Evaluated {len(drafts)} drafts. Selected Draft {winner_idx} as the superior architecture.\n\nReasoning: {response}"]
        }
