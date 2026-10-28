"""Validation of lease requests."""
import re

MAX_TTL = 3600
NAME_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")


def check_ttl(ttl):
    if ttl <= 0 or ttl > MAX_TTL:
        raise ValueError("ttl out of range")
    return ttl


def check_name(name):
    if not NAME_RE.fullmatch(name):
        raise ValueError("bad lease name")
    return name
