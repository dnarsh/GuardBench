"""Discount arithmetic in whole cents."""


class CouponError(Exception):
    pass


def apply_percent(price, percent):
    """Price after percent off, rounded down to whole cents; never below zero."""
    if price < 0:
        raise ValueError("price must not be negative")
    off = price * percent // 100
    return max(price - off, 0)


def format_price(cents):
    """1234 -> '12.34'."""
    return "%d.%02d" % divmod(cents, 100)


def savings(price, percent):
    """Cents saved by the discount."""
    return price - apply_percent(price, percent)
