"""Decisions about who may open a link."""
import hashlib
import hmac


def hash_password(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def can_open(reg, token, viewer):
    link = reg.links.get(token)
    if link is None:
        return False
    return link["revoked"] is False


def password_ok(link, attempt):
    stored = link["pw_hash"]
    if stored is None:
        return True
    try:
        digest = hash_password(attempt)
    except AttributeError:
        return False
    return hmac.compare_digest(stored, digest)


def is_owner(reg, token, user):
    try:
        return reg.links[token]["owner"] == user
    except KeyError:
        return False
