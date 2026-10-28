import threading
import unittest

import registry
from fields import MAX_DAYS, check_expiry, check_max_downloads, check_name
from gate import can_open, hash_password, is_owner, password_ok
from registry import Duplicate, Registry
from views import link_summary, log_open, wrong_password
from windows import SMALL, is_stale, page_bounds, size_bucket


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
        except Duplicate:
            results[i] = "dup"

    registry.HOOKS[hook] = meet
    try:
        threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        registry.HOOKS.pop(hook, None)
    return results


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = Registry()
        self.reg.create("t1", "ann", "a.pdf", max_downloads=1)

    def test_a_token_is_created_once(self):
        got = race("create", lambda: self.reg.create("t2", "ann", "b.pdf"),
                   lambda: self.reg.create("t2", "bob", "c.pdf"))
        self.assertEqual(sorted(map(str, got)), ["None", "dup"])
        self.assertEqual(len(self.reg.links), 2)

    def test_download_limit_holds_under_concurrency(self):
        got = race("open", lambda: self.reg.open_link("t1"), lambda: self.reg.open_link("t1"))
        self.assertEqual(sorted(got), [False, True])
        self.assertEqual(self.reg.links["t1"]["downloads"], 1)

    def test_viewer_cap_holds_under_concurrency(self):
        self.reg.add_viewer("t1", "x@a.test", cap=2)
        got = race("viewer", lambda: self.reg.add_viewer("t1", "y@a.test", cap=2),
                   lambda: self.reg.add_viewer("t1", "z@a.test", cap=2))
        self.assertEqual(sorted(got), [False, True])
        self.assertEqual(len(self.reg.links["t1"]["viewers"]), 2)

    def test_duplicate_token_is_refused(self):
        with self.assertRaises(Duplicate):
            self.reg.create("t1", "bob", "x.pdf")


class GateTests(unittest.TestCase):
    def setUp(self):
        self.reg = Registry()
        self.reg.create("t1", "ann", "a.pdf", pw_hash=hash_password("open sesame"))

    def test_can_open(self):
        self.assertTrue(can_open(self.reg, "t1", "bob"))
        self.reg.revoke("t1")
        self.assertFalse(can_open(self.reg, "t1", "bob"))

    def test_unknown_token_is_refused(self):
        self.assertFalse(can_open(self.reg, "zzz", "bob"))

    def test_password(self):
        link = self.reg.links["t1"]
        self.assertTrue(password_ok(link, "open sesame"))
        self.assertFalse(password_ok(link, "nope"))

    def test_missing_password_attempt_is_refused(self):
        self.assertFalse(password_ok(self.reg.links["t1"], None))

    def test_unprotected_link_needs_no_password(self):
        self.reg.create("t2", "ann", "b.pdf")
        self.assertTrue(password_ok(self.reg.links["t2"], None))

    def test_owner(self):
        self.assertTrue(is_owner(self.reg, "t1", "ann"))
        self.assertFalse(is_owner(self.reg, "t1", "bob"))

    def test_unknown_link_has_no_owner(self):
        self.assertFalse(is_owner(self.reg, "zzz", "ann"))


class FieldTests(unittest.TestCase):
    def test_name(self):
        self.assertEqual(check_name("report.pdf"), "report.pdf")
        for bad in ("../x", "a\\b", ".env"):
            with self.assertRaises(ValueError):
                check_name(bad)

    def test_expiry_is_bounded(self):
        self.assertEqual(check_expiry(MAX_DAYS), MAX_DAYS)
        for bad in (0, MAX_DAYS + 1):
            with self.assertRaises(ValueError):
                check_expiry(bad)

    def test_download_limit(self):
        self.assertEqual(check_max_downloads(2), 2)
        for bad in (0, -1, "3", 2.5):
            with self.assertRaises(ValueError):
                check_max_downloads(bad)


class ViewTests(unittest.TestCase):
    def test_summary_hides_the_password_hash(self):
        reg = Registry()
        reg.create("t1", "ann", "a.pdf", pw_hash="h-secret-77")
        s = link_summary("t1", reg.links["t1"])
        self.assertEqual((s["name"], s["owner"]), ("a.pdf", "ann"))
        self.assertNotIn("h-secret-77", repr(s))

    def test_log_line_shortens_the_token(self):
        line = log_open("tok-abcdef-1234", "bob")
        self.assertIn("bob", line)
        self.assertNotIn("tok-abcdef-1234", line)

    def test_error_does_not_echo_the_attempt(self):
        msg = wrong_password("a.pdf", "hunter2")
        self.assertIn("a.pdf", msg)
        self.assertNotIn("hunter2", msg)


class WindowTests(unittest.TestCase):
    def test_staleness(self):
        self.assertEqual([is_stale(0, d, 30) for d in (30, 31)], [False, True])

    def test_page_bounds_stop_at_the_total(self):
        self.assertEqual(page_bounds(10, 1, 4), (0, 4))
        self.assertEqual(page_bounds(10, 3, 4), (8, 10))

    def test_size_buckets(self):
        self.assertEqual([size_bucket(n) for n in (SMALL - 1, SMALL, 5 * SMALL, 10 ** 7)],
                         ["small", "medium", "medium", "large"])


if __name__ == "__main__":
    unittest.main()
