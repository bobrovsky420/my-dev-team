from functools import cached_property
from pathlib import Path
from devteam.extensions import CrewExtension, WorkspaceSaver, GitCommitter
from devteam.utils import WithLogging
from .execution import Execution
from .history import History

class VirtualCrew(WithLogging, Execution, History):
    """Orchestrator of a virtual crew."""

    def __init__(self,
                 project_folder: Path,
                 manager,
                 checkpointer,
                 *,
                 extensions: list[CrewExtension] = None,
                 workspace_saver: CrewExtension = None,
                 git_committer: CrewExtension = None):
        self.project_folder = project_folder
        self.manager = manager
        self.workspace_saver = workspace_saver or WorkspaceSaver(workspace_dir=project_folder)
        self.git_committer = git_committer or GitCommitter(workspace_dir=project_folder / 'workspace')
        self.extensions = extensions or []
        self.app = self.manager.build_graph(memory=checkpointer)

    @cached_property
    def system_hooks(self) -> list[CrewExtension]:
        return [
            self.workspace_saver,
            self.git_committer
        ]

    @cached_property
    def all_extensions(self) -> list[CrewExtension]:
        return self.system_hooks + self.extensions
