"""Webhook settings."""
import os


def load_secret(env=None):
    """Shared secret as bytes; empty bytes when unset."""
    env = os.environ if env is None else env
    return env.get("WEBHOOK_SECRET", "").encode()


def load_tolerance(env=None):
    """Seconds a delivery timestamp may be off; 300 unless WEBHOOK_TOLERANCE is a positive number."""
    env = os.environ if env is None else env
    raw = env.get("WEBHOOK_TOLERANCE", "")
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return 300
