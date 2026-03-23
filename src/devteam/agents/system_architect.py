from .schemas import SubmitArchitecture, SystemArchitectResponse
from .base_agent import BaseAgent

class SystemArchitect(BaseAgent[SystemArchitectResponse]):
    output_schema = SystemArchitectResponse
    tools = [SubmitArchitecture]
