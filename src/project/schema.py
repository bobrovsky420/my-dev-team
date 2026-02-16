from pydantic import BaseModel
from typing import List

class FinalReport(BaseModel):
    title: str
    content: str
    code_snippets: List[str]
    status: str
