"""Coupon code signing."""
import hashlib
import hmac

TAG_LEN = 8


def tag_for(secret, base):
    """Short HMAC tag of a coupon base code."""
    return hmac.new(secret, base.encode(), hashlib.sha256).hexdigest()[:TAG_LEN]


def make_code(secret, base):
    """'SAVE10' -> 'SAVE10-<tag>'."""
    return "%s-%s" % (base, tag_for(secret, base))


def check_code(secret, code):
    """Base code when the tag is valid, else None."""
    base, _, tag = code.rpartition("-")
    if not base:
        return None
    if not secret:
        return None
    if hmac.compare_digest(tag, tag_for(secret, base)):
        return base
    return None


def looks_like_code(text):
    """Cheap shape check before any cryptography: BASE-<8 hex digits>."""
    base, _, tag = text.rpartition("-")
    return bool(base) and len(tag) == TAG_LEN and all(c in "0123456789abcdef" for c in tag)
