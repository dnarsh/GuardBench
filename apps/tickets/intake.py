"""Checks on data that comes in from users."""
MAX_TITLE = 120
PRIORITIES = ("low", "normal", "high")


def check_new(title, body, priority):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title required")
    if len(title) > MAX_TITLE:
        raise ValueError("title too long")
    if priority not in PRIORITIES:
        raise ValueError("bad priority")
    return title.strip(), body or "", priority


def check_assignee(desk, name):
    if name not in desk.agents:
        raise ValueError("unknown agent")
    return name
