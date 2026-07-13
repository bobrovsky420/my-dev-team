from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, Union
from pydantic import BaseModel, ConfigDict, Field

class _BaseRunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    provider: str
    rpm: int = 0
    workflow: str = 'development'
    fanout: bool = False

class StartRequest(_BaseRunRequest):
    kind: Literal['start'] = 'start'
    project_name: str
    requirements: str
    seed_path: str | None = None

class ResumeRequest(_BaseRunRequest):
    kind: Literal['resume'] = 'resume'
    resume_thread: str
    feedback: str | None = None
    feedback_source: str = 'reviewer'
    checkpoint_id: str | None = None

RunRequest = Annotated[Union[StartRequest, ResumeRequest], Field(discriminator='kind')]

@dataclass
class RunHooks:
    callbacks: list[Any] = field(default_factory=list)
    extensions: list[Any] = field(default_factory=list)
