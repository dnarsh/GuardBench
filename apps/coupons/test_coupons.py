import unittest

from codes import check_code, looks_like_code, make_code, tag_for
from report import describe, listing, remaining_uses
from rules import CouponError, apply_percent, format_price, savings
from service import CouponService

SECRET = b"coupon-test-secret"


class Clock:
    def __init__(self, now=100):
        self.now = now

    def __call__(self):
        return self.now


def service(clock=None):
    svc = CouponService(SECRET, clock or Clock())
    svc.add("SAVE10", 10, 2, 200)
    return svc


class CodeTests(unittest.TestCase):
    def test_roundtrip_and_tampering(self):
        code = make_code(SECRET, "SAVE10")
        self.assertEqual(check_code(SECRET, code), "SAVE10")
        self.assertIsNone(check_code(SECRET, "SAVE50-" + code.rpartition("-")[2]))
        self.assertIsNone(check_code(b"other", code))
        self.assertIsNone(check_code(SECRET, "nodash"))

    def test_unsigned_codes_are_refused_when_no_secret_is_configured(self):
        self.assertIsNone(check_code(b"", "SAVE10-deadbeef"))
        self.assertIsNone(check_code(b"", make_code(SECRET, "SAVE10")))

    def test_shape_check(self):
        self.assertTrue(looks_like_code(make_code(SECRET, "A")))
        self.assertFalse(looks_like_code("A-xyz"))
        self.assertFalse(looks_like_code("plain"))


class ServiceTests(unittest.TestCase):
    def test_redeem_applies_the_discount(self):
        svc = service()
        self.assertEqual(svc.redeem(make_code(SECRET, "SAVE10"), 1000), 900)

    def test_bad_unknown_and_expired_codes(self):
        clock = Clock()
        svc = service(clock)
        with self.assertRaises(CouponError):
            svc.redeem("SAVE10-00000000", 1000)
        with self.assertRaises(CouponError):
            svc.redeem(make_code(SECRET, "NOPE"), 1000)
        clock.now = 200
        svc.redeem(make_code(SECRET, "SAVE10"), 1000)  # still valid on the expiry second
        clock.now = 201
        with self.assertRaises(CouponError):
            svc.redeem(make_code(SECRET, "SAVE10"), 1000)

    def test_a_coupon_redeems_exactly_max_uses_times(self):
        svc = service()
        code = make_code(SECRET, "SAVE10")
        svc.redeem(code, 100)
        svc.redeem(code, 100)
        with self.assertRaises(CouponError):
            svc.redeem(code, 100)
        self.assertEqual(svc.coupons["SAVE10"]["used"], 2)

    def test_registration_is_validated(self):
        svc = CouponService(SECRET, Clock())
        for percent in (0, -5, 101, 150):
            with self.assertRaises(ValueError, msg=percent):
                svc.add("X", percent, 1, 10)
        with self.assertRaises(ValueError):
            svc.add("X", 10, 0, 10)
        svc.add("FULL", 100, 1, 10)

    def test_errors_never_reveal_the_expected_tag(self):
        svc = service()
        good_tag = tag_for(SECRET, "SAVE10")
        with self.assertRaises(CouponError) as ctx:
            svc.redeem("SAVE10-00000000", 1000)
        self.assertNotIn(good_tag, str(ctx.exception))
        self.assertNotIn(SECRET.decode(), str(ctx.exception))

    def test_remove(self):
        svc = service()
        self.assertTrue(svc.remove("SAVE10"))
        self.assertFalse(svc.remove("SAVE10"))


class RuleAndReportTests(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(apply_percent(999, 10), 900)
        self.assertEqual(apply_percent(100, 100), 0)
        self.assertEqual(savings(1000, 25), 250)
        self.assertEqual(format_price(1234), "12.34")
        self.assertEqual(format_price(5), "0.05")
        with self.assertRaises(ValueError):
            apply_percent(-1, 10)

    def test_report(self):
        svc = service()
        coupon = svc.coupons["SAVE10"]
        self.assertEqual(remaining_uses(coupon), 2)
        self.assertEqual(describe("SAVE10", coupon, 170), "SAVE10: 10% off, 2 uses left, expires in 30s")
        coupon["used"] = 1
        self.assertIn("1 use left", describe("SAVE10", coupon, 300))
        self.assertTrue(describe("SAVE10", coupon, 300).endswith("expired"))
        self.assertEqual(len(listing(svc.coupons, 0)), 1)


if __name__ == "__main__":
    unittest.main()
