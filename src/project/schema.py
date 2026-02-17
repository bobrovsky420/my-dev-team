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

class FinalReport(BaseModel):
    """
    A final crew manager's report containing all deliverables from the team members
    """
    title: str
    content: str
    technical_specification: TechnicalSpecification
    code_snippets: List[str]
    review_feedback: str
    summary: str
    status: str
