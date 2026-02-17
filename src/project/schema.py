from pydantic import BaseModel
from typing import List, Optional

class TechnicalSpecification(BaseModel):
    """
    A technical specification for a project deliverable, including requirements and constraints
    """
    title: str
    description: str
    requirements: str
    constraints: Optional[str] = None
    edge_cases: Optional[str] = None
    additional_notes: Optional[str] = None

class SourceFile(BaseModel):
    """
    A source code file with its name and content
    """
    filename: str
    content: str

class DeveloperOutcome(BaseModel):
    """
    The expected output from a developer agent
    """
    source_files: List[SourceFile]
    commit_message: str

class FinalReport(BaseModel):
    """
    A final crew manager's report containing all deliverables from the team members
    """
    title: str
    content: str
    technical_specification: TechnicalSpecification
    developer_outcome: DeveloperOutcome
    review_feedback: str
    summary: str
    status: str
