from pathlib import Path

_CONFIG_DIR: Path = Path(__file__).parent / 'config'

def set_config_dir(path: Path) -> None:
    global _CONFIG_DIR
    _CONFIG_DIR = path.resolve()

def get_config_dir() -> Path:
    return _CONFIG_DIR
