from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class Project:
    original_mail: Dict
    tech_specification: Optional[str] = None
    source_code: Optional[str] = None
    file_extension: Optional[str] = None
    review_report: Optional[str] = None
    final_result: Optional[str] = None
