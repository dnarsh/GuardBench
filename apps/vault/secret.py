"""A secret value that refuses to show itself."""


class Secret:
    __slots__ = ("name", "_value", "version")

    def __init__(self, name, value, version=1):
        self.name = name
        self._value = value
        self.version = version

    def reveal(self):
        """The raw value; callers must not log it."""
        return self._value

    def __repr__(self):
        return "Secret(%s, v%d, ***)" % (self.name, self.version)

    __str__ = __repr__


def mask(value, keep=0):
    """'abcdef' -> '******'; keep > 0 leaves that many trailing characters visible."""
    if keep <= 0 or keep >= len(value):
        return "*" * len(value)
    return "*" * (len(value) - keep) + value[-keep:]
