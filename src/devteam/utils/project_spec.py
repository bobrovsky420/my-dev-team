import re
from datetime import datetime
from pathlib import Path

def parse_spec_from_string(content: str) -> tuple[str, str]:
    name = "New Project"
    lines = content.split('\n')
    spec_start = 0
    for idx, line in enumerate(lines):
        if not line.strip():
            spec_start = idx + 1
            break
        if line.startswith('Subject:') and 'NEW PROJECT:' in line:
            extracted_name = line.split('NEW PROJECT:', 1)[-1].strip()
            if extracted_name:
                name = extracted_name
    spec_content = '\n'.join(lines[spec_start:]).strip()
    return name, spec_content

def load_project_spec(path: str) -> tuple[str, str]:
    return parse_spec_from_string(Path(path).read_text(encoding='utf-8'))

def generate_thread_id(project_name: str) -> str:
    """Creates a unique, folder-safe thread ID."""
    safe_name = re.sub(r'[^a-z0-9]', '_', project_name.lower())
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'{safe_name}_{timestamp}'
