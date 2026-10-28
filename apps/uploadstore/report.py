"""Usage summaries."""
from quota import MAX_BYTES, MAX_FILES


def usage_line(count, size):
    """'2/3 files, 100/3072 bytes'."""
    return "%d/%d files, %d/%d bytes" % (count, MAX_FILES, size, MAX_FILES * MAX_BYTES)


def percent_full(count):
    return int(100 * count / MAX_FILES)


def is_full(count):
    return count >= MAX_FILES
