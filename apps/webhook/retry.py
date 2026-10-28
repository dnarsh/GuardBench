"""Delivery retry schedule for the sender side."""
BASE = 2
CAP = 300


def delay(attempt):
    """Seconds to wait before retry number `attempt` (1-based), doubling up to CAP."""
    if attempt < 1:
        raise ValueError("attempt starts at 1")
    return min(BASE ** attempt, CAP)


def schedule(attempts):
    return [delay(n) for n in range(1, attempts + 1)]
