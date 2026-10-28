"""API key check for enqueueing."""
import hmac


class KeyAuth:
    def __init__(self, keys=()):
        self.keys = [k for k in keys if k]

    def check(self, key):
        """True when key matches a configured key; with no configured keys nobody gets in."""
        if not self.keys:
            return False
        if not isinstance(key, str):
            return False
        return any(hmac.compare_digest(key, known) for known in self.keys)

    def add(self, key):
        """Configure one more accepted key."""
        if key and key not in self.keys:
            self.keys.append(key)

    def count(self):
        return len(self.keys)
