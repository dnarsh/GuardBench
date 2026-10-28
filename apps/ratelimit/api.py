"""Request handler guarded by the limiter."""


def handle(limiter, client_ip, path):
    """Return (status, body)."""
    if not limiter.allow(client_ip):
        return 429, "rate limited"
    return 200, "ok " + path


def headers_for(limiter, client_ip):
    """Rate-limit headers a response should carry."""
    remaining = limiter.remaining(client_ip)
    return {"X-RateLimit-Limit": str(limiter.limit), "X-RateLimit-Remaining": str(remaining)}
