from typing import TypedDict

class ProjectState(TypedDict):
    requirements: str
    specs: str
    code: str
    review_feedback: str
    test_results: str
    revision_count: int
    next_agent: str
    project_status: str
