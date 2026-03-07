import operator
from typing import Dict, TypedDict, Annotated, List

class ExecutionState(TypedDict):
    specs: str
    current_task: str
    workspace_files: Dict[str, str]
    review_feedback: str
    test_results: str
    revision_count: int
    communication_log: Annotated[List[str], operator.add]
