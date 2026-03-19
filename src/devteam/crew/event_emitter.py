from .events import Event

class EventEmitter:
    """Mixin for emitting events to extensions"""

    all_extensions: list

    def emit_event(self, event: Event, thread_id: str, **kwargs) -> dict | None:
        """Emit an event to all registered extensions."""
        method_name = f'on_{event}'
        merged = {}
        for ext in self.all_extensions:
            method = getattr(ext, method_name, None)
            if callable(method):
                result = method(thread_id, **kwargs)
                if isinstance(result, dict):
                    merged.update(result)
                    if result.get('abort_requested'):
                        break
        return merged or None
