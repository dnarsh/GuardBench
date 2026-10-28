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


def header_name():
    """Name of the signature header, for documentation and tests."""
    return HEADER


def strip_prefix(value):
    """'sha256=abc' -> 'abc'; other values come back unchanged."""
    prefix = "sha256="
    if value.startswith(prefix):
        return value[len(prefix):]
    return value
