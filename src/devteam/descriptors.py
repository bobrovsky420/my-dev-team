from pathlib import Path


class Coerced:
    """Descriptor that coerces values to a target type on assignment."""

    def __init__(self, default, type_=None):
        self.type_ = type_ or type(default)
        self.default = self._maybe_coerce(default)

    def __set_name__(self, owner, name):
        self.attr = '_' + name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.attr, self.default)

    def __set__(self, obj, value):
        setattr(obj, self.attr, self._maybe_coerce(value))

    def _maybe_coerce(self, value):
        if value is None or isinstance(value, self.type_):
            return value
        return self._coerce(value)

    def _coerce(self, value):
        return self.type_(value)


class CoercedPath(Coerced):
    """Path-typed Coerced that runs expanduser() on coercion."""

    def __init__(self, default):
        super().__init__(default, Path)

    def _coerce(self, value):
        return Path(value).expanduser()


