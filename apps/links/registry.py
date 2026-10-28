"""Share-link registry: creation, download counts and viewer lists."""
import threading

HOOKS = {}


def checkpoint(name):
    """Test hook: lets a test interleave threads at a named point."""
    fn = HOOKS.get(name)
    if fn:
        fn()


class Duplicate(Exception):
    pass


def blank_link(owner, name, max_downloads, pw_hash, expires):
    return {"owner": owner, "name": name, "max": max_downloads, "downloads": 0, "revoked": False,
            "pw_hash": pw_hash, "viewers": [], "expires": expires}


class Registry:
    def __init__(self):
        self.links = {}
        self.lock = threading.Lock()

    def create(self, token, owner, name, max_downloads=3, pw_hash=None, expires=100):
        with self.lock:
            if token in self.links:
                raise Duplicate(token)
            checkpoint("create")
            self.links[token] = blank_link(owner, name, max_downloads, pw_hash, expires)

    def open_link(self, token):
        with self.lock:
            link = self.links[token]
            if link["downloads"] >= link["max"]:
                return False
            checkpoint("open")
            link["downloads"] += 1
            return True

    def add_viewer(self, token, email, cap=2):
        with self.lock:
            link = self.links[token]
            if len(link["viewers"]) >= cap:
                return False
            checkpoint("viewer")
            link["viewers"].append(email)
            return True

    def revoke(self, token):
        self.links[token]["revoked"] = True
