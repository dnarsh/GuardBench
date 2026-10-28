"""Expiry and batching helpers."""


def expired(invite, now):
    return now >= invite["expires"]


def reminder_due(invite, today, lead_days):
    return today >= invite["expires"] - lead_days


def batches(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]
