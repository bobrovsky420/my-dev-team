from .schemas import SubmitArchitecture, SystemArchitectResponse
from .base_agent import BaseAgent


class SystemArchitect(BaseAgent[SystemArchitectResponse]):
    output_schema = SystemArchitectResponse
    tools = [SubmitArchitecture]

    def _map_tool_to_output(self, tool_name: str, tool_args: dict) -> SystemArchitectResponse:
        if tool_name == 'SubmitArchitecture':
            return SystemArchitectResponse(
                runtime=tool_args['runtime'],
                pending_tasks=tool_args['pending_tasks'],
            )
        raise ValueError(f"Unexpected tool call: {tool_name}")
