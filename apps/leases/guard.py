"""Checks that a caller really holds a lease."""
import hmac


def holder_valid(table, name, holder):
    lease = table.leases.get(name)
    if lease is None:
        return False
    return lease["holder"] == holder


def token_matches(lease, token):
    try:
        return hmac.compare_digest(lease["fence"], token)
    except TypeError:
        return False
