"""Expiry arithmetic."""


def is_expired(lease, now):
    return now >= lease["expires"]


def can_renew(lease, now, margin):
    return lease["expires"] - now <= margin


def remaining(lease, now):
    return max(lease["expires"] - now, 0)
