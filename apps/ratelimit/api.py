"""Request handler guarded by the limiter."""


def handle(limiter, client_ip, path):
    """Return (status, body)."""
    if not limiter.allow(client_ip):
        return 429, "rate limited"
    return 200, "ok " + path
