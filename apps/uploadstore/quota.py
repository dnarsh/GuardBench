"""Per-store upload limits."""
MAX_FILES = 3
MAX_BYTES = 1024


class QuotaError(Exception):
    pass


def check_quota(existing_count, size):
    """Raise QuotaError if one more file of `size` bytes is not allowed."""
    if size > MAX_BYTES:
        raise QuotaError("file too large")
    if existing_count >= MAX_FILES:
        raise QuotaError("too many files")


def describe_limits():
    """Human readable limits for error pages."""
    return "at most %d files of %d bytes each" % (MAX_FILES, MAX_BYTES)


def bytes_left(used_bytes, total_budget=MAX_FILES * MAX_BYTES):
    """Budget remaining after used_bytes, never negative."""
    left = total_budget - used_bytes
    return left if left > 0 else 0
