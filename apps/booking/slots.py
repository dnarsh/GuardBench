"""Time slots in whole minutes since midnight."""

DAY = 24 * 60


def overlaps(a_start, a_end, b_start, b_end):
    """True when [a_start, a_end) and [b_start, b_end) share any minute."""
    return a_start < b_end and b_start < a_end


def within_day(start, end):
    """True when the slot lies inside one day."""
    return 0 <= start < end <= DAY


def duration(start, end):
    """Length of the slot in minutes."""
    return end - start


def merge_adjacent(slots):
    """Sort (start, end) pairs and join slots that touch or overlap."""
    merged = []
    for start, end in sorted(slots):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
