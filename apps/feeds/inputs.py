"""Validation of subscription requests."""
MAX_ITEMS = 50


def check_feed_url(url):
    if not url.startswith(("http://", "https://")):
        raise ValueError("unsupported scheme")
    return url


def check_limit(n):
    if n < 1 or n > MAX_ITEMS:
        raise ValueError("limit out of range")
    return n
