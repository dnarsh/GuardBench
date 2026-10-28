"""Secret names."""
import re

NAME_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")


def is_valid_name(name):
    """Lower-case letters, digits, dot, dash and underscore; starts with a letter."""
    return isinstance(name, str) and bool(NAME_RE.match(name))


def namespace(name):
    """'db.password' -> 'db'; names without a dot are their own namespace."""
    return name.split(".", 1)[0]


def normalize(name):
    """Strip and lower-case user input before validating it."""
    return name.strip().lower()
