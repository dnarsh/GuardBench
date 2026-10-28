import threading
import unittest

import meter as meter_mod
from authz import feature_enabled, is_staff, may_adjust
from cycle import cycle_end, days_remaining, in_cycle, prorate
from invoice import charge_failed, invoice_row, invoice_title, total_used
from meter import Meter, QuotaExceeded
from plans import check_bytes, check_plan, cheapest_with


def race(hook, *calls):
    """Run calls in threads that meet at the named hook; return their results."""
    barrier = threading.Barrier(len(calls), timeout=0.3)

    def meet():
        try:
            barrier.wait()
        except threading.BrokenBarrierError:
            pass

    results = [None] * len(calls)

    def run(i, fn):
        try:
            results[i] = fn()
        except QuotaExceeded:
            results[i] = "over"

    meter_mod.HOOKS[hook] = meet
    try:
        threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        meter_mod.HOOKS.pop(hook, None)
    return results


class MeterTests(unittest.TestCase):
    def setUp(self):
        self.m = Meter()
        self.m.add_account("acme", "pro", 100, "tok_live_998877")

    def test_usage_never_exceeds_the_limit(self):
        got = race("reserve", lambda: self.m.reserve("acme", 60), lambda: self.m.reserve("acme", 60))
        self.assertEqual(sorted(map(str, got)), ["None", "over"])
        self.assertEqual(self.m.accounts["acme"]["used"], 60)

    def test_invoice_numbers_are_distinct(self):
        got = race("invoice", self.m.next_invoice, self.m.next_invoice)
        self.assertEqual(len(set(got)), 2)

    def test_usage_text_and_headroom(self):
        self.m.reserve("acme", 40)
        self.assertEqual(self.m.usage("acme"), "40 of 100 bytes")
        self.assertEqual(self.m.headroom("acme"), 60)

    def test_reserve_up_to_the_limit_and_release(self):
        self.m.reserve("acme", 100)
        with self.assertRaises(QuotaExceeded):
            self.m.reserve("acme", 1)
        self.m.release("acme", 500)
        self.assertEqual(self.m.accounts["acme"]["used"], 0)


class AuthzTests(unittest.TestCase):
    def setUp(self):
        self.m = Meter()
        self.m.staff = {"bea": "billing", "dan": "support"}
        self.m.add_account("acme", "pro", 100, "tok")

    def test_who_may_adjust(self):
        self.assertTrue(may_adjust(self.m, "bea"))
        self.assertFalse(may_adjust(self.m, "dan"))

    def test_strangers_may_not_adjust(self):
        self.assertFalse(may_adjust(self.m, "mallory"))

    def test_features_follow_the_plan(self):
        self.assertTrue(feature_enabled(self.m, "acme", "export"))
        self.assertFalse(feature_enabled(self.m, "acme", "audit"))

    def test_staff_membership(self):
        self.assertTrue(is_staff(self.m, "dan"))
        self.assertFalse(is_staff(self.m, "mallory"))

    def test_unknown_account_has_no_features(self):
        self.assertFalse(feature_enabled(self.m, "ghost", "share"))


class PlanTests(unittest.TestCase):
    def test_plans(self):
        self.assertEqual(check_plan("team"), "team")
        with self.assertRaises(ValueError):
            check_plan("platinum")

    def test_cheapest_plan_with_a_feature(self):
        self.assertEqual(cheapest_with("export"), "pro")
        self.assertIsNone(cheapest_with("teleport"))

    def test_sizes(self):
        self.assertEqual(check_bytes(0), 0)
        for bad in (-1, 1.5, "7"):
            with self.assertRaises(ValueError):
                check_bytes(bad)


class InvoiceTests(unittest.TestCase):
    def test_row_hides_the_card_token(self):
        acct = {"plan": "pro", "used": 5, "card_token": "tok_live_998877"}
        row = invoice_row("acme", acct)
        self.assertEqual((row["account"], row["used"]), ("acme", 5))
        self.assertNotIn("tok_live_998877", repr(row))

    def test_charge_failure_shows_only_the_last_four(self):
        msg = charge_failed("acme", "4242424242424242")
        self.assertIn("4242", msg)
        self.assertNotIn("4242424242424242", msg)

    def test_total(self):
        self.assertEqual(total_used([{"used": 2}, {"used": 3}]), 5)

    def test_title(self):
        self.assertEqual(invoice_title(1004), "INV-1004")


class CycleTests(unittest.TestCase):
    def test_cycle_is_half_open(self):
        self.assertEqual([in_cycle(d, 1, 30) for d in (0, 1, 30, 31)], [False, True, True, False])

    def test_today_counts_as_remaining(self):
        self.assertEqual([days_remaining(10, e) for e in (10, 12)], [1, 3])

    def test_cycle_end(self):
        self.assertEqual(cycle_end(1, 30), 30)

    def test_prorate(self):
        self.assertEqual(prorate(300, 10, 30), 100)


if __name__ == "__main__":
    unittest.main()
