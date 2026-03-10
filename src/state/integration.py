import operator
from typing import NotRequired, TypedDict, Annotated, Dict, List

class IntegrationState(TypedDict):
    requirements: str
    specs: str
    workspace_files: Dict[str, str]
    test_results: str
    integration_bugs: List[str]
    total_revisions: int
    final_report: str
    abort_requested: NotRequired[bool]
    communication_log: Annotated[List[str], operator.add]
