import operator
from typing import Any, Dict, TypedDict, Annotated, List, NotRequired, Literal

def add_ints(a: int, b: int) -> int:
    """Safe reducer for accumulating integers across tasks."""
    return (a or 0) + (b or 0)

ProjectPhase = Literal['planning', 'development', 'integration', 'complete']

class ProjectState(TypedDict):
    current_phase: ProjectPhase
    requirements: str
    specs: str
    human_answer: str
    clarification_question: str
    runtime: str
    pending_tasks: List[Dict[str, Any]]
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
    error: NotRequired[bool]
    error_message: NotRequired[str]
