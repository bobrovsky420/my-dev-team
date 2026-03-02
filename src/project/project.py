from typing import Annotated, TypedDict
import operator

class ProjectState(TypedDict):
    requirements: str
    pending_tasks: list[str]
    current_task: str
    completed_tasks: list[str]
    clarification_question: str
    human_answer: str
    specs: str
    code_drafts: Annotated[list[str], operator.add]
    winner_index: int
    task_phase: str
    code: str
    review_feedback: str
    test_results: str
    revision_count: int
    next_agent: str
    project_status: str
    final_report: str
    communication_log: Annotated[list[str], operator.add]
