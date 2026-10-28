"""Block list consulted on every validation."""


class BackendError(Exception):
    """The remote block list could not be reached."""


class BlockList:
    def __init__(self, blocked=(), backend=None):
        self.blocked = set(blocked)
        self.backend = backend  # optional callable user -> bool; may raise BackendError

    def is_blocked(self, user):
        """True when the user must not hold a session."""
        if user in self.blocked:
            return True
        if self.backend is not None:
            return bool(self.backend(user))
        return False

    def block(self, user):
        self.blocked.add(user)

    def unblock(self, user):
        self.blocked.discard(user)

    def size(self):
        """Number of locally blocked users."""
        return len(self.blocked)
