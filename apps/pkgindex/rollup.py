"""Download windows and rankings."""


def in_last_days(day, today, days):
    return 0 <= today - day < days


def top_n(counts, n):
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:n]


def total(counts):
    return sum(counts.values())
