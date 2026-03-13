import docker
from docker.errors import ContainerError, ImageNotFound
from pathlib import Path

class DockerSandbox:
    def __init__(self, image: str = 'python:3.12-slim'):
        self.image = image
        try:
            self.client = docker.from_env()
            self.client.images.get(self.image)
        except ImageNotFound:
            print(f"🐳 Pulling {self.image} (this only happens once)...")
            self.client.images.pull(self.image)
        except Exception as e:
            raise RuntimeError(f"Could not connect to Docker. Is Docker Desktop running? Error: {e}")

    def run_tests(self, workspace_dir: Path, timeout: int = 15) -> str:
        absolute_workspace = workspace_dir.resolve()
        command = "bash -c 'pip install pytest --quiet --disable-pip-version-check --root-user-action=ignore && pytest -v'"
        try:
            container = self.client.containers.run(
                image=self.image,
                command=command,
                volumes={str(absolute_workspace): {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                network_disabled=False,
                mem_limit="256m",
                nano_cpus=1_000_000_000,
                environment={
                    "PYTHONUNBUFFERED": "1",
                    "PYTHONPATH": "/workspace"
                },
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
        except Exception as e:
            return f"⚠️ Sandbox Execution Error: {str(e)}"
