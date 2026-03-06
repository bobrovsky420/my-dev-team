import operator
from typing import TypedDict, Annotated, List

class ExecutionState(TypedDict):
    specs: str
    current_task: str
    existing_code: str
    code: str
    review_feedback: str
    test_results: str
    revision_count: int
    communication_log: Annotated[List[str], operator.add]
