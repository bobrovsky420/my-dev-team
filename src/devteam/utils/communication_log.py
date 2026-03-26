
class CommunicationLog:
    """Mixin to provide logging capabilities to agents and tools."""

    def communication(self, message: str | list[str]) -> list[str]:
        if isinstance(message, str):
            return [f"**[{self.__class__.__name__}]**: {message}"]
        return [f"**[{self.__class__.__name__}]**: {msg}" for msg in message]
