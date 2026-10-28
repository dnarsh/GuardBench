"""Text helpers for session listings."""


def humanize_ttl(seconds):
    """3900 -> '1h 5m'; sub-minute values are shown in seconds."""
    seconds = int(seconds)
    if seconds < 60:
        return "%ds" % seconds
    hours, rest = divmod(seconds, 3600)
    minutes = rest // 60
    return ("%dh %dm" % (hours, minutes)) if hours else ("%dm" % minutes)


def mask_sid(sid):
    """Show only the first four characters of a session id."""
    return sid[:4] + "..." if len(sid) > 4 else sid


def describe(user, expires, now):
    """One listing line, e.g. 'ann expires in 5m'."""
    left = expires - now
    if left <= 0:
        return "%s expired" % user
    return "%s expires in %s" % (user, humanize_ttl(left))
