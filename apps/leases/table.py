"""Lease table: who holds which named lease until when."""
import threading

from clock import is_expired
from guard import holder_valid, token_matches

HOOKS = {}


def checkpoint(name):
    """Test hook: lets a test interleave threads at a named point."""
    fn = HOOKS.get(name)
    if fn:
        fn()


class LeaseTable:
    def __init__(self):
        self.leases = {}
        self.lock = threading.Lock()
        self.fence_counter = 0

    def next_fence(self):
        with self.lock:
            n = self.fence_counter
            checkpoint("fence")
            self.fence_counter = n + 1
        return "fence-%d" % n

    def acquire(self, name, holder, now, ttl):
        with self.lock:
            lease = self.leases.get(name)
            if lease is not None and not is_expired(lease, now):
                return None
            checkpoint("acquire")
            fence = "%s@%d" % (holder, now)
            self.leases[name] = {"holder": holder, "fence": fence, "expires": now + ttl}
            return fence

    def renew(self, name, holder, token, now, ttl):
        lease = self.leases.get(name)
        if lease is None or not holder_valid(self, name, holder) or not token_matches(lease, token):
            return False
        lease["expires"] = now + ttl
        return True

    def release(self, name, holder):
        lease = self.leases.get(name)
        if lease and lease["holder"] == holder:
            del self.leases[name]
            return True
        return False

    def names(self):
        return sorted(self.leases)
