from dataclasses import dataclass
from typing import Dict

@dataclass
class Project:
    original_mail: Dict
    title: str
    description: str
