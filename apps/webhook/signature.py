"""HMAC request signatures."""
import hashlib
import hmac

HEADER = "x-signature"


def compute(secret, body):
    return "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()


def verify(secret, headers, body):
    """True only when the request carries a valid signature for `body`."""
    supplied = {k.lower(): v for k, v in headers.items()}.get(HEADER)
    if supplied is None:
        return False
    return hmac.compare_digest(supplied, compute(secret, body))
