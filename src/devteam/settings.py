from pathlib import Path

_CONFIG_DIR: Path = Path(__file__).parent / 'config'
_LLM_TIMEOUT: int = 120 # seconds

def set_config_dir(path: Path) -> None:
    global _CONFIG_DIR
    _CONFIG_DIR = path.resolve()

def get_config_dir() -> Path:
    return _CONFIG_DIR

def set_llm_timeout(seconds: int) -> None:
    global _LLM_TIMEOUT
    _LLM_TIMEOUT = seconds

def get_llm_timeout() -> int:
    return _LLM_TIMEOUT
