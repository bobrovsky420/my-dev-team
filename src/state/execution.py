import operator
from typing import TypedDict, Annotated, List

class ExecutionState(TypedDict):
    specs: str
    current_task: str
    existing_main_code: str
    existing_test_code: str
    existing_additional_files: str
    main_code: str
    test_code: str
    additional_files: str
    review_feedback: str
    test_results: str
    revision_count: int
    communication_log: Annotated[List[str], operator.add]
