"""Validation of link settings."""
MAX_DAYS = 90


def check_name(name):
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValueError("bad name")
    return name


def check_expiry(days):
    if days < 1 or days > MAX_DAYS:
        raise ValueError("expiry out of range")
    return days


def check_max_downloads(n):
    if not isinstance(n, int) or n < 1:
        raise ValueError("max downloads must be a positive integer")
    return n
