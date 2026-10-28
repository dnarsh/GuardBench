"""Display names for stored files."""
import re

SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def display_name(name, limit=40):
    """Name made safe for logs and HTML: unsafe runs become '_', long names are cut in the middle."""
    cleaned = SAFE_RE.sub("_", name).strip("_") or "unnamed"
    if len(cleaned) <= limit:
        return cleaned
    keep = (limit - 3) // 2
    return cleaned[:keep] + "..." + cleaned[-keep:]


def unique_name(name, taken):
    """name, or name-2, name-3 ... when already taken."""
    if name not in taken:
        return name
    stem, dot, ext = name.partition(".")
    n = 2
    while "%s-%d%s%s" % (stem, n, dot, ext) in taken:
        n += 1
    return "%s-%d%s%s" % (stem, n, dot, ext)
