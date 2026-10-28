"""Webhook settings."""
import os


def load_secret(env=None):
    """Shared secret as bytes; empty bytes when unset."""
    env = os.environ if env is None else env
    return env.get("WEBHOOK_SECRET", "").encode()
