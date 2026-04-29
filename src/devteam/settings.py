from functools import cached_property
from pathlib import Path
import re
import yaml
from .descriptors import Coerced, CoercedPath

_LOCAL_CONFIG_PATH = Path('config.yaml')
_GLOBAL_CONFIG_PATH = Path.home() / '.devteam' / 'config.yaml'


class Settings:
    config_dir: Path = Path(__file__).parent / 'config'

    workspace_dir = CoercedPath('workspaces')
    skills_dir = CoercedPath('skills')
    llm_timeout = Coerced(120)
    llm_streaming = Coerced(False)
    provider = Coerced('ollama')
    rpm = Coerced(0)
    no_docker = Coerced(False)
    ask_approval = Coerced(False)
    rag_mcp_url = Coerced('http://localhost:8000/mcp')
    rag_mcp_tool = Coerced('qdrant-find')
    rag_collection = Coerced(None, str)
    rag_enabled = Coerced(True)
    max_revision_count = Coerced(3)
    no_ask = Coerced(False)
    no_complexity_routing = Coerced(False)

    @cached_property
    def tools_config_dir(self) -> Path:
        return self.config_dir / 'tools'

    def load(self, config_path: Path = None) -> None:
        paths = [config_path] if config_path else [_GLOBAL_CONFIG_PATH, _LOCAL_CONFIG_PATH]
        fields = {name for name, attr in vars(type(self)).items() if isinstance(attr, Coerced)}
        for path in paths:
            if not path.exists():
                continue
            with open(path) as f:
                cfg = yaml.safe_load(f) or {}
            for key, value in cfg.items():
                normalized = re.sub(r' +', '_', key.lower())
                if normalized in fields:
                    setattr(self, normalized, value)


settings = Settings()
