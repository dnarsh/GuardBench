"""Webhook endpoint: verify the signature, then parse the event."""
import json

from signature import compute, verify


def handle(secret, headers, body):
    """Return (status, text)."""
    if not secret:
        return 500, "server misconfigured"
    if not verify(secret, headers, body):
        return 401, "bad signature"
    try:
        event = json.loads(body)
    except ValueError:
        return 400, "bad json"
    kind = event.get("type", "unknown") if isinstance(event, dict) else "unknown"
    return 200, "received " + str(kind)


def describe_status(status):
    """Reason phrase for the statuses handle() can return."""
    phrases = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 500: "Server Error"}
    return phrases.get(status, "Unknown")
