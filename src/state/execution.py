import operator
from typing import TypedDict, Annotated, List

class ExecutionState(TypedDict):
    specs: str
    current_task: str
    existing_code: str
    code_drafts: List[str] # Overwritten per task phase, so no operator.add
    winner_index: int
    task_phase: str
    code: str
    review_feedback: str
    test_results: str
    revision_count: int
    communication_log: Annotated[List[str], operator.add]
