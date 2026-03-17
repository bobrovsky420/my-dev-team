"""Streamlit-compatible extension that pushes crew execution events into a queue."""

import logging
import time
from queue import Queue
from .base_extension import CrewExtension

logger = logging.getLogger(__name__)

# Event types
EVT_START = 'start'
EVT_RESUME = 'resume'
EVT_STEP = 'step'
EVT_PAUSE = 'pause'
EVT_FINISH = 'finish'
EVT_ERROR = 'error'


class StreamlitLogger(CrewExtension):
    """Extension that publishes execution events to a thread-safe queue.

    The Streamlit app reads from this queue to render real-time progress.
    """

    def __init__(self, event_queue: Queue):
        self.queue = event_queue

    def _emit(self, event_type: str, **data):
        logger.debug("StreamlitLogger emitting event: %s", event_type)
        self.queue.put({
            'type': event_type,
            'ts': time.time(),
            **data,
        })

    def on_start(self, thread_id: str, initial_state: dict):
        self._emit(EVT_START, thread_id=thread_id, state=initial_state)

    def on_resume(self, thread_id: str, state_update: dict):
        self._emit(EVT_RESUME, thread_id=thread_id, state_update=state_update)

    def on_step(self, thread_id: str, state_update: dict, full_state: dict):
        self._emit(EVT_STEP, thread_id=thread_id,
                   state_update=state_update, full_state=full_state)

    def on_pause(self, thread_id: str, current_state: dict, next_node: str) -> dict | None:
        self._emit(EVT_PAUSE, thread_id=thread_id, next_node=next_node)
        return None  # Streamlit handles HITL via its own UI

    def on_finish(self, thread_id: str, final_state: dict):
        if final_state.get('error'):
            self._emit(EVT_ERROR, thread_id=thread_id, state=final_state)
        else:
            self._emit(EVT_FINISH, thread_id=thread_id, state=final_state)
