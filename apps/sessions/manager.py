"""Session creation and validation."""
import secrets
import threading

from policy import BackendError

MIN_TTL = 60
MAX_TTL = 86400


def _checkpoint():
    """No-op hook between the limit check and the insert; tests interleave threads here."""


class SessionLimit(Exception):
    pass


class SessionManager:
    def __init__(self, store, policy, clock, ttl=3600, max_per_user=3):
        self.store = store
        self.policy = policy
        self.clock = clock
        self.ttl = ttl
        self.max_per_user = max_per_user
        self._lock = threading.Lock()

    def create(self, user, ttl=None):
        """Open a session for user and return its id."""
        if not isinstance(user, str) or not user.strip():
            raise ValueError("user must be a non-empty string")
        ttl = self.ttl if ttl is None else ttl
        if not MIN_TTL <= ttl <= MAX_TTL:
            raise ValueError("ttl out of range")
        with self._lock:
            if self.store.count_for(user, self.clock()) >= self.max_per_user:
                raise SessionLimit(user)
            _checkpoint()
            sid = secrets.token_hex(8)
            self.store.put(sid, user, self.clock() + ttl)
        return sid

    def validate(self, sid):
        """User name for a live, unblocked session, else None."""
        record = self.store.get(sid)
        if record is None:
            return None
        user, expires = record
        if self.clock() >= expires:
            self.store.delete(sid)
            return None
        try:
            blocked = self.policy.is_blocked(user)
        except BackendError:
            blocked = True  # cannot tell, so refuse
        return None if blocked else user

    def revoke_all(self, user):
        """End every session of the user."""
        return self.store.drop_user(user)
