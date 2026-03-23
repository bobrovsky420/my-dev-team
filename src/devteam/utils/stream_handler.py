import sys
from langchain_core.callbacks import BaseCallbackHandler

class StreamHandler(BaseCallbackHandler):
    """Streams raw LLM token output (including thinking) to the console."""

    def __init__(self, file=None):
        self._file = file or sys.stderr
        self._current_agent = None
        self._in_thinking = False

    def _write_agent_header(self, tags):
        agent = next(
            (tag.split(':', maxsplit=1)[1] for tag in tags if isinstance(tag, str) and tag.startswith('node:')),
            None
        )
        if agent and agent != self._current_agent:
            self._current_agent = agent
            self._file.write(f"\n--- [{agent}] ---\n")

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        tags = kwargs.get('tags', [])
        self._write_agent_header(tags)
        chunk = kwargs.get('chunk')
        if chunk and hasattr(chunk, 'message'):
            reasoning = chunk.message.additional_kwargs.get('reasoning_content', '')
            if reasoning:
                if not self._in_thinking:
                    self._in_thinking = True
                    self._file.write('<think>\n')
                self._file.write(reasoning)
                self._file.flush()
                return
            if self._in_thinking:
                self._in_thinking = False
                self._file.write('\n</think>\n')
        self._file.write(token)
        self._file.flush()

    def on_llm_end(self, response, **kwargs) -> None:
        if self._in_thinking:
            self._in_thinking = False
            self._file.write('\n</think>\n')
        self._file.write("\n")
        self._file.flush()
