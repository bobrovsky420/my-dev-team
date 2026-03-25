from pathlib import Path

# pylint: disable=global-statement

_WORKSPACES_DIR = Path('workspaces')
_CONFIG_DIR: Path = Path(__file__).parent / 'config'
_LLM_TIMEOUT: int = 120 # seconds
_LLM_STREAMING: bool = False
_NO_DOCKER: bool = False

def set_no_docker(enabled: bool) -> None:
    global _NO_DOCKER
    _NO_DOCKER = enabled

def get_no_docker() -> bool:
    return _NO_DOCKER

def set_workspaces_dir(path: Path) -> None:
    global _WORKSPACES_DIR
    _WORKSPACES_DIR = path.resolve()

def get_workspaces_dir() -> Path:
    return _WORKSPACES_DIR

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

def set_llm_streaming(enabled: bool) -> None:
    global _LLM_STREAMING
    _LLM_STREAMING = enabled

def get_llm_streaming() -> bool:
    return _LLM_STREAMING
