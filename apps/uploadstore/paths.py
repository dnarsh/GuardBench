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


def extension(name):
    """Lower-case extension including the dot, or an empty string."""
    base = os.path.basename(name)
    dot = base.rfind(".")
    return base[dot:].lower() if dot > 0 else ""


def is_hidden(name):
    """True when any path component starts with a dot."""
    parts = [part for part in name.split("/") if part]
    return any(part.startswith(".") for part in parts)
