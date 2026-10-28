"""Validation of package names and versions."""
import re

NAME_RE = re.compile(r"[a-z][a-z0-9-]{1,39}")


def check_name(name):
    if not NAME_RE.fullmatch(name):
        raise ValueError("bad package name")
    return name


def check_version(text):
    parts = text.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError("bad version")
    return text


def normalise(name):
    return name.strip().lower().replace("_", "-")
