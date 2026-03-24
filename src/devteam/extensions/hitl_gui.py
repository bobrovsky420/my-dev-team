import threading
import time
from queue import Queue
from .base_extension import CrewExtension

class HumanInTheLoopGUI(CrewExtension):
    """Extension that pauses the workflow to get human input via the Streamlit GUI."""

    def __init__(self, event_queue: Queue):
        self.event_queue = event_queue
        self._response_event = threading.Event()
        self._response: str | None = None
        self._aborted = False

    def submit_response(self, response: str):
        """Called from the Streamlit UI when the user submits their answer."""
        self._response = response
        self._aborted = False
        self._response_event.set()

    def abort(self):
        """Called from the Streamlit UI when the user wants to abort."""
        self._response = None
        self._aborted = True
        self._response_event.set()

    def on_pause(self, thread_id: str, current_state: dict, next_node: str) -> dict | None:
        if next_node != 'human':
            return None
        question = current_state.get('clarification_question', 'The team needs your input.')
        self.event_queue.put({
            'type': 'hitl_request',
            'thread_id': thread_id,
            'question': question,
            'ts': time.time(),
        })
        self._response_event.clear()
        self._response_event.wait()
        if self._aborted:
            return {
                'abort_requested': True,
                'communication_log': ["**[Human]**: Aborted the workflow."]
            }
        return {
            'human_answer': self._response,
            'communication_log': [f"**[Human]**: {self._response}"]
        }
