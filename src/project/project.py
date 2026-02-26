from typing import Annotated, TypedDict
import operator

class ProjectState(TypedDict):
    requirements: str
    clarification_question: str
    human_answer: str
    specs: str
    code: str
    review_feedback: str
    test_results: str
    revision_count: int
    next_agent: str
    project_status: str
    final_report: str
    communication_log: Annotated[list[str], operator.add]
