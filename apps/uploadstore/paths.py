"""Resolve user supplied names inside the storage root."""
import os


def safe_join(root, name):
    """Return the absolute path of `name` under `root`, or raise ValueError."""
    if not name or "\x00" in name:
        raise ValueError("invalid name")
    root = os.path.realpath(root)
    full = os.path.realpath(os.path.join(root, name))
    if os.path.commonpath([root, full]) != root:
        raise ValueError("path escapes storage root")
    return full
