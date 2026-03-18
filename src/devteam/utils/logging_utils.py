import logging
import sys

LOG_FILE_NAME = 'mycrew.log'

class ConsoleDispatchFormatter(logging.Formatter):
    """Custom formatter for console output."""

    def __init__(self):
        super().__init__()
        self.root_formatter = logging.Formatter(fmt='%(message)s')
        self.default_formatter = logging.Formatter(fmt='%(name)s: %(message)s')

    def format(self, record):
        if record.name == 'root':
            return self.root_formatter.format(record)
        return self.default_formatter.format(record)

def setup_logging(*, file_level=logging.DEBUG, console_level=logging.INFO):
    file_handler = logging.FileHandler(LOG_FILE_NAME, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    file_handler.setFormatter(file_formatter)
    handlers = [file_handler]
    if console_level is not None:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(ConsoleDispatchFormatter())
        handlers.append(console_handler)
    logging.basicConfig(level=logging.DEBUG, handlers=handlers)

    # Disable annoying debug logs from libraries

    logging.getLogger('aiosqlite').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('LiteLLM').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
