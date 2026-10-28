"""Package index: packages, versions, yanking and download counts."""
import threading

HOOKS = {}


def checkpoint(name):
    """Test hook: lets a test interleave threads at a named point."""
    fn = HOOKS.get(name)
    if fn:
        fn()


class Exists(Exception):
    pass


class Index:
    def __init__(self):
        self.packages = {}
        self.owners = {}
        self.api_keys = {}
        self.lock = threading.Lock()

    def register(self, name, owner, upload_token):
        self.packages[name] = {"versions": {}, "upload_token": upload_token}
        self.owners[name] = {owner}

    def publish(self, name, version):
        with self.lock:
            versions = self.packages[name]["versions"]
            if version in versions:
                raise Exists(version)
            checkpoint("publish")
            versions[version] = {"yanked": False, "downloads": 0}

    def record_download(self, name, version):
        with self.lock:
            rec = self.packages[name]["versions"][version]
            n = rec["downloads"]
            checkpoint("download")
            rec["downloads"] = n + 1

    def yank(self, name, version):
        self.packages[name]["versions"][version]["yanked"] = True

    def latest(self, name):
        live = [v for v, rec in self.packages[name]["versions"].items() if not rec["yanked"]]
        return max(live, key=lambda v: tuple(int(p) for p in v.split("."))) if live else None

    def downloads(self, name, version):
        return self.packages[name]["versions"][version]["downloads"]
