import re
from typing import List, Optional

def sanitize_for_prompt(content: str, protected_tags: Optional[List[str]] = None) -> str:
    """
    Cleans raw file content and text before injecting it into an LLM prompt.
    """
    if not content:
        return ''
    safe_content = content
    if protected_tags:
        for tag in protected_tags:
            closing_tag = f'</{tag}>'
            safe_closing = f'&lt;/{tag}&gt;'
            safe_content = safe_content.replace(closing_tag, safe_closing)
    safe_content = re.sub(
        r'data:image\/[^;]+;base64,[a-zA-Z0-9+/]+=*',
        '[BASE64_DATA_REMOVED_TO_SAVE_TOKENS]',
        safe_content
    )
    safe_content = re.sub(r'\n{3,}', '\n\n', safe_content)
    safe_content = safe_content.replace('\x00', '')
    return safe_content.strip()
