"""Digest sizes and send intervals."""


def digest_slice(items, limit):
    return items[:limit]


def is_due(last_sent, now, interval):
    return now - last_sent >= interval


def newest_first(items):
    return sorted(items, key=lambda item: item["day"], reverse=True)
