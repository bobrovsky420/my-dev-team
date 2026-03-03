from pathlib import Path
import yaml

base_dir = Path('skills')
file_name = 'SKILL.md'

def load_skill_as_agent(skill_folder: Path) -> dict:
    """Parses a SKILL.md file and returns a configuration dictionary for BaseAgent."""
    skill_file = base_dir / skill_folder / file_name
    content = skill_file.read_text(encoding='utf-8')
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError(f"Invalid SKILL.md format in {skill_folder}. Missing YAML frontmatter.")
    frontmatter = yaml.safe_load(parts[1])
    instructions = parts[2].strip()
    return {
        'name': frontmatter.get('name', 'Unknown'),
        'model': frontmatter.get('model', 'ollama/qwen3:8b'),
        'temperature': frontmatter.get('temperature', 0.3),
        'prompt': instructions
    }
