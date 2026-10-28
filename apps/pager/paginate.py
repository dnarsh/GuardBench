"""Page arithmetic."""

MAX_SIZE = 100
DEFAULT_SIZE = 20


def validate_args(page, size):
    """Return (page, size) or raise ValueError."""
    for value in (page, size):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("page and size must be integers")
    if page < 1:
        raise ValueError("page starts at 1")
    if size < 1 or size > MAX_SIZE:
        raise ValueError("size must be between 1 and %d" % MAX_SIZE)
    return page, size


def page_slice(items, page, size):
    """Items of 1-based `page`."""
    start = (page - 1) * size
    return items[start:start + size]


def page_count(total, size):
    """Number of pages needed for total items (0 when empty)."""
    return -(-total // size)


def has_next(total, page, size):
    """True when a page after `page` exists."""
    return page * size < total
