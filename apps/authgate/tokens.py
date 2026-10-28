"""Signed session tokens: issue and verify (HMAC-SHA256)."""
import base64
import hashlib
import hmac
import time


def _sign(secret, payload):
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()


def issue(secret, user, ttl=3600, now=None):
    now = int(time.time() if now is None else now)
    payload = "%s|%d" % (user, now + ttl)
    raw = "%s|%s" % (payload, _sign(secret, payload))
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify(secret, token, now=None):
    """Return the user name for a valid, unexpired token, else None."""
    now = int(time.time() if now is None else now)
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        user, expires, sig = raw.rsplit("|", 2)
        good = hmac.compare_digest(sig, _sign(secret, "%s|%s" % (user, expires)))
        if good and int(expires) > now:
            return user
    except (ValueError, UnicodeError):
        pass
    return None
