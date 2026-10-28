"""Staleness, paging bounds and size buckets."""
SMALL = 1024
MEDIUM = 1024 * 1024


def is_stale(last_open, today, idle_days):
    return today - last_open > idle_days


def page_bounds(total, page, per_page):
    start = (page - 1) * per_page
    stop = min(start + per_page, total)
    return start, stop


def size_bucket(nbytes):
    if nbytes < SMALL:
        return "small"
    if nbytes < MEDIUM:
        return "medium"
    return "large"
