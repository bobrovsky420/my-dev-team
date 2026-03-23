import sys
from langchain_core.callbacks import BaseCallbackHandler

class StreamHandler(BaseCallbackHandler):
    """Streams raw LLM token output (including thinking) to the console."""

    def __init__(self, file=None):
        self._file = file or sys.stderr
        self._in_thinking = False

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        chunk = kwargs.get('chunk')
        if chunk and hasattr(chunk, 'message'):
            reasoning = chunk.message.additional_kwargs.get('reasoning_content', '')
            if reasoning:
                if not self._in_thinking:
                    self._in_thinking = True
                self._file.write(reasoning)
                self._file.flush()
                return
            if self._in_thinking:
                self._in_thinking = False
        self._file.write(token)
        self._file.flush()

    def on_llm_end(self, response, **kwargs) -> None:
        if self._in_thinking:
            self._in_thinking = False
        self._file.write("\n")
        self._file.flush()
