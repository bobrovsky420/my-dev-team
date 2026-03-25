import logging
import sys
from logging.handlers import RotatingFileHandler

LOG_FILE_NAME = 'mycrew.log'
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB

LOG_BACKUP_COUNT = 3

NOISY_LOGGERS = [
    'aiosqlite',
    'asyncio',
    'httpx',
    'httpcore',
    'LiteLLM',
    'urllib3.connectionpool',
]

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
    file_handler = RotatingFileHandler(
        LOG_FILE_NAME,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.doRollover() # Rotate on every start
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

    for noisy_logger in NOISY_LOGGERS:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
