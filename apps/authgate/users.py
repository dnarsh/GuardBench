"""User record helpers."""
import hashlib
import re

NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,31}$")
MIN_PASSWORD = 10


def normalize_name(name):
    """Lower-case and strip a user name; raise ValueError when it is not acceptable."""
    cleaned = name.strip().lower()
    if not NAME_RE.match(cleaned):
        raise ValueError("invalid user name")
    return cleaned


def password_problems(password):
    """List of reasons the password is too weak (empty list when acceptable)."""
    problems = []
    if len(password) < MIN_PASSWORD:
        problems.append("too short")
    if password.lower() == password:
        problems.append("needs an upper-case letter")
    if not any(ch.isdigit() for ch in password):
        problems.append("needs a digit")
    return problems


def make_record(name, password):
    """(name, sha256 hex) ready for AuthService users."""
    problems = password_problems(password)
    if problems:
        raise ValueError("weak password: " + ", ".join(problems))
    return normalize_name(name), hashlib.sha256(password.encode()).hexdigest()
