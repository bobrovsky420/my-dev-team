import operator
from typing import Dict, TypedDict, Annotated, List, NotRequired

class ProjectLifecycleState(TypedDict):
    requirements: str
    specs: str
    pending_tasks: List[str]
    workspace_files: Dict[str,str]
    total_revisions: int
    final_report: str
    integration_bugs: List[str]
    abort_requested: NotRequired[bool]
    communication_log: Annotated[List[str], operator.add]
