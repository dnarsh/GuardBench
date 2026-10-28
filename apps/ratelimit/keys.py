"""Normalise client identifiers into limiter keys."""


def client_key(ip, user=None):
    """Key a request by user when known, else by IP; IPv4-mapped IPv6 maps to IPv4."""
    if user:
        return "user:" + user.strip().lower()
    ip = ip.strip().lower()
    if ip.startswith("::ffff:"):
        ip = ip[7:]
    return "ip:" + ip


def split_key(key):
    """Inverse of client_key: ('ip' or 'user', value)."""
    kind, _, value = key.partition(":")
    return kind, value
