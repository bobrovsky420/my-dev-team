import operator
from typing import Dict, TypedDict, Annotated, List, NotRequired

def add_ints(a: int, b: int) -> int:
    """Safe reducer for accumulating integers across tasks."""
    return (a or 0) + (b or 0)

class ProjectState(TypedDict):
    requirements: str
    specs: str
    human_answer: str
    clarification_question: str
    runtime: str
    pending_tasks: List[str]
    workspace_files: Dict[str, str]
    current_task_index: int
    current_task: str
    review_feedback: str
    test_results: str
    revision_count: int
    total_revisions: Annotated[int, add_ints]
    final_report: str
    integration_bugs: List[str]
    communication_log: Annotated[List[str], operator.add]
    abort_requested: NotRequired[bool]
