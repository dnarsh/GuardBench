"""Coupon catalog and redemption."""
from codes import check_code
from rules import CouponError, apply_percent


class CouponService:
    def __init__(self, secret, clock):
        self.secret = secret
        self.clock = clock
        self.coupons = {}  # base code -> {"percent", "max_uses", "expires", "used"}

    def add(self, base, percent, max_uses, expires):
        """Register a coupon valid through `expires` (inclusive)."""
        if not 0 < percent <= 100:
            raise ValueError("percent must be in 1..100")
        if max_uses < 1:
            raise ValueError("max_uses must be at least 1")
        self.coupons[base] = {"percent": percent, "max_uses": max_uses,
                              "expires": expires, "used": 0}

    def redeem(self, code, price):
        """Price after the coupon's discount; CouponError when it cannot be redeemed."""
        base = check_code(self.secret, code)
        if base is None:
            raise CouponError("bad signature")
        coupon = self.coupons.get(base)
        if coupon is None:
            raise CouponError("unknown coupon")
        if self.clock() > coupon["expires"]:
            raise CouponError("expired")
        if coupon["used"] >= coupon["max_uses"]:
            raise CouponError("exhausted")
        coupon["used"] += 1
        return apply_percent(price, coupon["percent"])

    def remove(self, base):
        """Delete a coupon; True when it existed."""
        return self.coupons.pop(base, None) is not None
