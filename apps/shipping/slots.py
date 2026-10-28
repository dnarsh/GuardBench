"""Time windows, storage fees and history tails."""
FREE_DAYS = 5


def fits_window(minute, start, end):
    return start <= minute < end


def storage_due(received, today):
    return today - received > FREE_DAYS


def tail(events, n):
    return events[max(len(events) - n, 0):]
