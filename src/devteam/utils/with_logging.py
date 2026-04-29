import logging
from functools import cached_property

class WithLogging:
    """Mixin to provide logging capabilities to agents and tools."""

    @cached_property
    def logger(self) -> logging.Logger:
        cls_name = self.__class__.__name__
        node = getattr(self, 'node_name', None)
        return logging.getLogger(f"{cls_name}.{node}" if node else cls_name)
