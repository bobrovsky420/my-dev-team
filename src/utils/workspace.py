from .sanitizer import sanitize_for_prompt

def workspace_str_from_files(workspace_files: dict) -> str:
    workspace_str = ''
    for filepath, content in workspace_files.items():
        clean_content = sanitize_for_prompt(content, [filepath, 'workspace'])
        workspace_str += f"--- FILE: {filepath} ---\n{clean_content}\n\n"
    return workspace_str
