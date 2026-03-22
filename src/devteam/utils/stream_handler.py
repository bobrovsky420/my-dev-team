import sys
from langchain_core.callbacks import BaseCallbackHandler

class StreamHandler(BaseCallbackHandler):
    """Streams raw LLM token output (including thinking) to the console."""

    def __init__(self, file=None):
        self._file = file or sys.stderr
        self._current_agent = None

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        tags = kwargs.get('tags', [])
        agent = next(
            (tag.split(':', maxsplit=1)[1] for tag in tags if isinstance(tag, str) and tag.startswith('node:')),
            None
        )
        if agent and agent != self._current_agent:
            self._current_agent = agent
            self._file.write(f"\n--- [{agent}] ---\n")
        self._file.write(token)
        self._file.flush()

    def on_llm_end(self, response, **kwargs) -> None:
        self._file.write("\n")
        self._file.flush()
