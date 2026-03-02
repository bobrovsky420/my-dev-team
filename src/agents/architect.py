import re
from .base import BaseAgent

class SystemArchitect(BaseAgent):
    def process(self, state: dict) -> dict:
        self.logger.info("Designing the execution plan...")
        specs = state.get('specs', '')
        response = self.invoke_llm(specs=specs)
        raw_tasks = re.findall(r"<task>(.*?)</task>", response, re.IGNORECASE | re.DOTALL)
        tasks = [t.strip() for t in raw_tasks if t.strip()]
        if not tasks:
            self.logger.warning("Failed to generate <task> tags. Defaulting to a single monolithic task.")
            tasks = ["Implement the entire application according to the provided specifications."]
        self.logger.info("Successfully broke the project down into %i tasks.", len(tasks))
        plan_log = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
        return {
            'pending_tasks': tasks,
            'communication_log': [f"Created sequential implementation plan:\n{plan_log}"]
        }
