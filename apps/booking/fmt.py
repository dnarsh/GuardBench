"""Text for schedules."""


def fmt_time(minutes):
    """570 -> '09:30'."""
    return "%02d:%02d" % divmod(minutes, 60)


def fmt_slot(start, end):
    """'09:00-10:30 (90 min)'."""
    return "%s-%s (%d min)" % (fmt_time(start), fmt_time(end), end - start)


def agenda(entries):
    """One line per (start, end, who) entry."""
    return ["%s %s" % (fmt_slot(s, e), who) for s, e, who in entries]
