from pydantic import BaseModel, Field, field_validator, model_validator
from devteam.utils.sanitizer import normalize_workspace_content

# pylint: disable=line-too-long

class ProductManagerResponse(BaseModel):
    clarification_question: str | None = Field(
        default=None,
        description="Provide exactly ONE clarifying question ONLY if the requirements are too vague to determine the tech stack or core features. Leave null if requirements are clear."
    )
    specs: str | None = Field(
        default=None,
        description="Provide detailed Technical Specifications ONLY if the requirements are clear. Must be formatted in clean Markdown with sections for architecture, features, acceptance criteria, constraints, and testing. MUST end with an '## Alignment Confirmation' section."
    )

    @model_validator(mode='after')
    def validate_response(self):
        has_question = bool((self.clarification_question or '').strip())
        has_specs = bool((self.specs or '').strip())
        if has_question == has_specs:
            raise ValueError("Exactly one of 'clarification_question' or 'specs' must be provided, and the other must be empty.")
        return self

class DevelopmentTask(BaseModel):
    task_name: str = Field(
        description="A clear, concise name for the task."
    )
    user_story: str = Field(
        description="The user story describing the 'why' and 'what' (e.g., 'As a user, I want to...')."
    )
    acceptance_criteria: list[str] = Field(
        min_length=1,
        description="A bulleted list of specific, testable conditions that must be met for this task to be considered complete."
    )

class SystemArchitectResponse(BaseModel):
    runtime: str = Field(description="The primary runtime environment for this project (e.g., 'python', 'node', 'java', etc.)")
    pending_tasks: list[DevelopmentTask] = Field(
        min_length=1,
        description="A sequential backlog of development tasks required to build the project."
    )

class WorkspaceFile(BaseModel):
    path: str = Field(
        description="The relative path to the file, including the filename and extension (e.g., 'src/main.py' or 'tests/test_main.py')."
    )
    content: str = Field(
        description="The ENTIRE, 100% complete source code or text for this file. NEVER use placeholders like '// ... existing code ...' or '# ... previous logic ...'. If you omit existing lines from a modified file, that logic will be permanently deleted."
    )

    @field_validator('content', mode='before')
    @classmethod
    def normalize_content(cls, value):
        if isinstance(value, str):
            return normalize_workspace_content(value)
        return value

class DeveloperResponse(BaseModel):
    workspace_files: list[WorkspaceFile] = Field(
        default_factory=list,
        description="A list of files that were created or modified during this task. Do NOT include existing files from the workspace that do not need to be modified."
    )

class CodeReviewerResponse(BaseModel):
    review_feedback: str = Field(
        description="Must be exactly 'APPROVED' if the code perfectly meets all criteria. If it fails, provide a newline-separated list of bugs formatted exactly as: '- [File Path] - [Bug/Missing Logic]: Description of why it fails.'"
    )

class CodeJudgeResponse(BaseModel):
    winner_index: int = Field(
        default=0,
        description="The integer index of the winning draft (e.g., 0, 1, or 2). Must be a valid index from the provided drafts."
    )

class QAEngineerResponse(BaseModel):
    test_results: str = Field(
        description="Must be exactly 'PASSED' if the logic for the current task is completely sound, handles edge cases, and passes all simulated tests. If the logic fails, misses edge cases, or has poorly written tests, provide a detailed bug report containing failed test scenarios and referencing specific file paths, formatted with newlines."
    )

class FinalQAResponse(BaseModel):
    evaluation_summary: str = Field(
        description="Your step-by-step mental simulation, edge-case analysis, and reasoning for why the code passes or fails."
    )
    test_results: str = Field(
        description="Must be exactly 'PASSED' if the logic for the current task is completely sound, handles edge cases, and passes all simulated tests. If it fails, provide a detailed bug report."
    )

class FinalReportResponse(BaseModel):
    final_report: str = Field(
        description="A detailed Final Markdown Report for the stakeholders. Must include 4 sections: 1. Executive Summary. 2. Technical Architecture. 3. Development & QA History (a chronological narrative of bugs and revisions). 4. Final Deliverables (workspace files rendered into markdown code blocks with file paths)."
    )
