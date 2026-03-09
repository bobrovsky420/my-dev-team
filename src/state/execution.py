import operator
from typing import Dict, TypedDict, Annotated, List, NotRequired

class ExecutionState(TypedDict):
    specs: str
    current_task: str
    workspace_files: Dict[str, str]
    review_feedback: str
    test_results: str
    revision_count: int
    abort_requested: NotRequired[bool]
    communication_log: Annotated[List[str], operator.add]
