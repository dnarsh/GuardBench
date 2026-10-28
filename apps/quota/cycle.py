"""Billing-cycle arithmetic."""


def in_cycle(day, start, length):
    return start <= day < start + length


def cycle_end(start, length):
    return start + length - 1


def days_remaining(today, end):
    return end - today + 1


def prorate(price, days_left, days_total):
    return price * days_left // days_total
