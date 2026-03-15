from functools import cached_property
from importlib import resources
from pathlib import Path
import logging
import docker
from docker.errors import ImageNotFound
import yaml

class DockerSandbox:
    def __init__(self):
        self.logger = logging.getLogger('Docker Sandbox')
        try:
            self.client = docker.from_env()
        except Exception as e: # pylint: disable=broad-exception-caught
            raise RuntimeError(f"Could not connect to Docker. Error: {e}") from e

    @cached_property
    def sandbox_config(self) -> dict:
        return yaml.safe_load(resources.files('devteam.config').joinpath('sandbox.yaml').read_text(encoding='utf-8'))

    @cached_property
    def runtimes(self) -> dict:
        return self.sandbox_config.get('runtimes', {})

    def pull_image(self, image: str):
        try:
            self.client.images.get(image)
        except ImageNotFound:
            self.logger.info("Pulling %s (this only happens once)...", image)
            self.client.images.pull(image)

    def run_tests(self, workspace_dir: Path, runtime: str = 'python', timeout: int = 15) -> str:
        absolute_workspace = workspace_dir.resolve()
        config = self.runtimes.get(runtime.lower())
        if not config:
            return f"⚠️ Sandbox Error: Unsupported runtime '{runtime}'. Supported runtimes: {list(self.runtimes.keys())}"
        self.pull_image(config['image'])
        try:
            container = self.client.containers.run(
                image=config['image'],
                command=config['command'],
                volumes={str(absolute_workspace): {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                network_disabled=False,
                mem_limit=config.get('mem_limit', '256m'),
                nano_cpus=1_000_000_000,
                detach=True
            )
            result = container.wait(timeout=timeout)
            exit_code = result['StatusCode']
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            container.remove()
            if exit_code == 0:
                return f"✅ Tests Passed:\n{logs}"
            else:
                return f"❌ Tests Failed (Exit Code {exit_code}):\n{logs}"
        except Exception as e: # pylint: disable=broad-exception-caught
            return f"⚠️ Sandbox Execution Error: {str(e)}"
