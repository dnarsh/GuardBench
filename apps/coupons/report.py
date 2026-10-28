"""Coupon listings for the admin page."""


def remaining_uses(coupon):
    """Redemptions left, never negative."""
    return max(coupon["max_uses"] - coupon["used"], 0)


def describe(base, coupon, now):
    """'SAVE10: 10% off, 1 use left, expires in 30s'."""
    left = remaining_uses(coupon)
    ttl = coupon["expires"] - now
    when = "expired" if ttl < 0 else "expires in %ds" % ttl
    plural = "" if left == 1 else "s"
    return "%s: %d%% off, %d use%s left, %s" % (base, coupon["percent"], left, plural, when)


def listing(coupons, now):
    """One line per coupon, sorted by base code."""
    return [describe(base, coupons[base], now) for base in sorted(coupons)]
