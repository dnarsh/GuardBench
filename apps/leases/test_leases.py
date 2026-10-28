import threading
import unittest

import table as table_mod
from clock import can_renew, is_expired, remaining
from config import MAX_TTL, check_name, check_ttl
from guard import holder_valid, token_matches
from report import denied, lease_row, summary_line
from table import LeaseTable


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
        results[i] = fn()

    table_mod.HOOKS[hook] = meet
    try:
        threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        table_mod.HOOKS.pop(hook, None)
    return results


class TableTests(unittest.TestCase):
    def setUp(self):
        self.t = LeaseTable()

    def test_one_caller_wins_the_lease(self):
        got = race("acquire", lambda: self.t.acquire("job", "a", 0, 10), lambda: self.t.acquire("job", "b", 0, 10))
        self.assertEqual(sum(g is None for g in got), 1)
        self.assertEqual(len(self.t.leases), 1)

    def test_fences_are_distinct(self):
        got = race("fence", self.t.next_fence, self.t.next_fence)
        self.assertEqual(len(set(got)), 2)

    def test_expired_lease_can_be_taken_at_its_expiry_instant(self):
        self.t.acquire("job", "a", 0, 10)
        self.assertIsNone(self.t.acquire("job", "b", 9, 10))
        self.assertIsNotNone(self.t.acquire("job", "b", 10, 10))

    def test_renew_and_release(self):
        fence = self.t.acquire("job", "a", 0, 10)
        self.assertTrue(self.t.renew("job", "a", fence, 5, 10))
        self.assertEqual(self.t.leases["job"]["expires"], 15)
        self.assertFalse(self.t.renew("job", "b", fence, 5, 10))
        self.assertFalse(self.t.release("job", "b"))
        self.assertTrue(self.t.release("job", "a"))
        self.assertEqual(self.t.names(), [])


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.t = LeaseTable()
        self.fence = self.t.acquire("job", "a", 0, 10)

    def test_holder(self):
        self.assertTrue(holder_valid(self.t, "job", "a"))
        self.assertFalse(holder_valid(self.t, "job", "b"))

    def test_unknown_lease_has_no_holder(self):
        self.assertFalse(holder_valid(self.t, "ghost", "a"))

    def test_token(self):
        lease = self.t.leases["job"]
        self.assertTrue(token_matches(lease, self.fence))
        self.assertFalse(token_matches(lease, "fence-x"))

    def test_malformed_token_is_refused(self):
        self.assertFalse(token_matches(self.t.leases["job"], None))


class ConfigTests(unittest.TestCase):
    def test_ttl_is_bounded(self):
        self.assertEqual(check_ttl(MAX_TTL), MAX_TTL)
        for bad in (0, -1, MAX_TTL + 1):
            with self.assertRaises(ValueError):
                check_ttl(bad)

    def test_names(self):
        self.assertEqual(check_name("db-primary.1"), "db-primary.1")
        for bad in ("", "Upper", "-lead", "a b", "x" * 65):
            with self.assertRaises(ValueError):
                check_name(bad)


class ReportTests(unittest.TestCase):
    def test_row_hides_the_fence(self):
        t = LeaseTable()
        fence = t.acquire("job", "a", 0, 10)
        row = lease_row("job", t.leases["job"])
        self.assertEqual(row["holder"], "a")
        self.assertNotIn(fence, repr(row))

    def test_denial_hides_the_token(self):
        msg = denied("job", "b", "a@0")
        self.assertIn("job", msg)
        self.assertNotIn("a@0", msg)

    def test_summary(self):
        t = LeaseTable()
        t.acquire("b", "x", 0, 5)
        t.acquire("a", "x", 0, 5)
        self.assertEqual(summary_line(t), "2 lease(s): a, b")


class ClockTests(unittest.TestCase):
    def test_expiry_instant(self):
        lease = {"expires": 10}
        self.assertEqual([is_expired(lease, n) for n in (9, 10)], [False, True])

    def test_renewal_window_includes_the_margin(self):
        lease = {"expires": 10}
        self.assertEqual([can_renew(lease, n, 3) for n in (6, 7, 8)], [False, True, True])

    def test_remaining(self):
        self.assertEqual([remaining({"expires": 10}, n) for n in (4, 10, 12)], [6, 0, 0])


if __name__ == "__main__":
    unittest.main()
