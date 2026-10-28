"""Validation of invite requests."""
ROLES = ("member", "admin")
MAX_TTL_DAYS = 30


def check_email(email):
    email = email.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("bad email")
    return email


def check_role(role):
    if role not in ROLES:
        raise ValueError("bad role")
    return role


def check_ttl(days):
    if not 1 <= days <= MAX_TTL_DAYS:
        raise ValueError("ttl out of range")
    return days
