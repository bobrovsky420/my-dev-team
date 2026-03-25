import logging
from functools import cached_property

class WithLogging:
    """Mixin to provide logging capabilities to agents and tools."""

    @cached_property
    def logger(self) -> logging.Logger:
        logger_name = f"{self.__class__.__name__}"
        return logging.getLogger(logger_name)
