"""Versioned secret store with access control and compare-and-set."""
import threading

from names import is_valid_name
from secret import Secret


def _checkpoint():
    """No-op hook between the version check and the write; tests interleave threads here."""


class AccessDenied(Exception):
    pass


class VersionConflict(Exception):
    pass


class Vault:
    def __init__(self, acl):
        self.acl = acl
        self._items = {}
        self._lock = threading.Lock()
        self.log = []

    def set(self, name, value, expected_version=None):
        """Store value and return its new version; with expected_version the write
        only succeeds when that is the current version (0 for a new secret)."""
        if not is_valid_name(name):
            raise ValueError("invalid secret name")
        if not isinstance(value, str) or not value:
            raise ValueError("value must be a non-empty string")
        with self._lock:
            current = self._items.get(name)
            have = current.version if current else 0
            if expected_version is not None and expected_version != have:
                raise VersionConflict(name)
            _checkpoint()
            self._items[name] = Secret(name, value, have + 1)
            self.log.append("set %s v%d" % (name, have + 1))
        return have + 1

    def get(self, user, name):
        """Secret value for a user who may read it."""
        if not self.acl.can_read(user, name):
            self.log.append("denied %s %s" % (user, name))
            raise AccessDenied("%s may not read %s" % (user, name))
        item = self._items.get(name)
        if item is None:
            raise KeyError(name)
        self.log.append("read %s by %s" % (name, user))
        return item.reveal()

    def names(self, user):
        """Names the user may read, sorted."""
        return sorted(n for n in self._items if self.acl.can_read(user, n))

    def delete(self, name):
        """Remove a secret; True when it existed."""
        return self._items.pop(name, None) is not None
