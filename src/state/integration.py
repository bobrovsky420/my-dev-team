import operator
from typing import NotRequired, TypedDict, Annotated, List

class IntegrationState(TypedDict):
    requirements: str
    specs: str
    code: str
    test_results: str
    integration_bugs: List[str]
    deployment_scripts: str
    final_report: str
    abort_requested: NotRequired[bool]
    communication_log: Annotated[List[str], operator.add]
