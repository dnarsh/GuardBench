"""Flat file store with name and quota checks."""
import os

from paths import safe_join
from quota import check_quota


class Store:
    def __init__(self, root):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def names(self):
        return sorted(os.listdir(self.root))

    def save(self, name, data):
        path = safe_join(self.root, name)
        check_quota(len(self.names()), len(data))
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def load(self, name):
        with open(safe_join(self.root, name), "rb") as fh:
            return fh.read()

    def delete(self, name):
        os.remove(safe_join(self.root, name))

    def usage(self):
        """(file count, total bytes) of everything stored."""
        sizes = [os.path.getsize(os.path.join(self.root, n)) for n in self.names()]
        return len(sizes), sum(sizes)
