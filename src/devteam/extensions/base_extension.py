from devteam.utils import WithLogging

class CrewExtension(WithLogging):
    """Base class for all Virtual Crew extensions."""

    def on_start(self, thread_id: str, initial_state: dict):
        """Triggered right before the crew starts running."""
        pass

    def on_resume(self, thread_id: str, state_update: dict):
        """Triggered when resuming an existing workflow."""
        pass

    def on_step(self, thread_id: str, state_update: dict, full_state: dict):
        """Triggered every time LangGraph updates the state."""
        pass

    def on_pause(self, thread_id: str, current_state: dict, next_node: str) -> dict | None:
        """Triggered when the graph pauses (e.g. waiting for HITL)."""
        pass

    def on_finish(self, thread_id: str, final_state: dict):
        """Triggered when the project successfully completes."""
        pass
