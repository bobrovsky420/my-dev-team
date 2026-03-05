import operator
from typing import TypedDict, Annotated, List

class PlanningState(TypedDict):
    requirements: str
    human_answer: str
    clarification_question: str
    specs: str
    pending_tasks: List[str]
    communication_log: Annotated[List[str], operator.add]
