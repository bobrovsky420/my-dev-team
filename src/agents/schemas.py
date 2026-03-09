from pydantic import BaseModel, Field, model_validator

class ProductManagerResponse(BaseModel):
    clarification_question: str | None = None
    specs: str | None = None

    @model_validator(mode='after')
    def validate_response(self):
        has_question = bool((self.clarification_question or '').strip())
        has_specs = bool((self.specs or '').strip())
        if has_question == has_specs:
            raise ValueError("Exactly one of 'clarification_question' or 'specs' must be provided, and the other must be empty.")
        return self

class SystemArchitectResponse(BaseModel):
    pending_tasks: list[str] = Field(min_length=1)

class WorkspaceFile(BaseModel):
    path: str
    content: str

class DeveloperResponse(BaseModel):
    workspace_files: list[WorkspaceFile] = Field(default_factory=list)

class CodeReviewerResponse(BaseModel):
    review_feedback: str

class QAEngineerResponse(BaseModel):
    test_results: str

class FinalReportResponse(BaseModel):
    final_report: str
