from devteam.state import ProjectState
from devteam.utils import sanitizer
from .schemas import ReporterResponse
from .base_agent import BaseAgent

class Reporter(BaseAgent[ReporterResponse]):
    output_schema = ReporterResponse

    def _input_history(self, state: ProjectState) -> str:
        return sanitizer.sanitize_for_prompt('\n\n'.join(state.communication_log), ['history'])
