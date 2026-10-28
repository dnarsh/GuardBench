"""Thread-safe fixed-window rate limiter."""
import threading
import time

from config import DEFAULT_LIMIT, DEFAULT_WINDOW
from store import WindowStore


def _checkpoint():
    """No-op hook between the check and the update; tests use it to interleave threads."""


class RateLimiter:
    def __init__(self, limit=DEFAULT_LIMIT, window=DEFAULT_WINDOW, clock=time.time):
        self.limit = limit
        self.clock = clock
        self.store = WindowStore(window)
        self._lock = threading.Lock()

    def allow(self, key):
        """Count one request for key; False once the window's limit is used up."""
        with self._lock:
            now = self.clock()
            if self.store.count(key, now) >= self.limit:
                return False
            _checkpoint()
            self.store.incr(key, now)
            return True
