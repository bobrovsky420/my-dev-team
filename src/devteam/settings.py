from pathlib import Path

class Settings:
    def __init__(self):
        self._settings = {
            'WORKSPACES_DIR': Path('workspaces'),
            'CONFIG_DIR': Path(__file__).parent / 'config',
            'LLM_TIMEOUT': 120,  # seconds
            'LLM_STREAMING': False,
            'NO_DOCKER': False,
        }

    @property
    def workspace_dir(self) -> Path:
        return self._settings['WORKSPACES_DIR']

    @workspace_dir.setter
    def workspace_dir(self, path: Path) -> None:
        self._settings['WORKSPACES_DIR'] = path.resolve()

    @property
    def config_dir(self) -> Path:
        return self._settings['CONFIG_DIR']

    @config_dir.setter
    def config_dir(self, path: Path) -> None:
        self._settings['CONFIG_DIR'] = path.resolve()

    @property
    def llm_timeout(self) -> int:
        return self._settings['LLM_TIMEOUT']

    @llm_timeout.setter
    def llm_timeout(self, seconds: int) -> None:
        self._settings['LLM_TIMEOUT'] = seconds

    @property
    def llm_streaming(self) -> bool:
        return self._settings['LLM_STREAMING']

    @llm_streaming.setter
    def llm_streaming(self, enabled: bool) -> None:
        self._settings['LLM_STREAMING'] = enabled

    @property
    def no_docker(self) -> bool:
        return self._settings['NO_DOCKER']

    @no_docker.setter
    def no_docker(self, enabled: bool) -> None:
        self._settings['NO_DOCKER'] = enabled


settings = Settings()
