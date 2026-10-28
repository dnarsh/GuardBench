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
