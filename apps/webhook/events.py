"""Event helpers."""
KNOWN = {"ping", "push", "release", "star"}


def event_type(event):
    """Type string of a parsed event, or 'unknown'."""
    if isinstance(event, dict):
        return str(event.get("type", "unknown"))
    return "unknown"


def is_known(kind):
    return kind in KNOWN


def summarize(event):
    """Short log line for an event; never includes the payload body."""
    kind = event_type(event)
    size = len(event) if isinstance(event, dict) else 0
    return "%s (%d fields)" % (kind, size)
