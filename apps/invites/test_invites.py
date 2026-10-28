import threading
import unittest

import store
from access import domain_ok, may_invite, verify_code
from forms import MAX_TTL_DAYS, check_email, check_role, check_ttl
from render import accept_error, describe_invite, member_row
from store import SeatsFull, Workspace
from window import batches, expired, reminder_due


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
        except SeatsFull:
            results[i] = "full"

    store.HOOKS[hook] = meet
    try:
        threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        store.HOOKS.pop(hook, None)
    return results


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace("boss@acme.test", seats=2)

    def test_a_code_is_accepted_once(self):
        self.ws.create_invite("c1", "x@acme.test", "member", 10)
        got = race("accept", lambda: self.ws.accept("c1", "x@acme.test"),
                   lambda: self.ws.accept("c1", "y@acme.test"))
        self.assertEqual(sorted(got), [False, True])
        self.assertEqual(len(self.ws.members), 2)

    def test_seat_limit_holds_under_concurrency(self):
        got = race("seat", lambda: self.ws.add_member("a@acme.test", "member"),
                   lambda: self.ws.add_member("b@acme.test", "member"))
        self.assertEqual(sorted(map(str, got)), ["None", "full"])
        self.assertEqual(len(self.ws.members), 2)

    def test_issued_codes_are_distinct(self):
        codes = race("issue", self.ws.issue_code, self.ws.issue_code)
        self.assertEqual(len(set(codes)), 2)

    def test_accept_adds_the_member(self):
        self.ws.create_invite("c1", "x@acme.test", "admin", 10)
        self.assertTrue(self.ws.accept("c1", "x@acme.test"))
        self.assertEqual(self.ws.members["x@acme.test"]["role"], "admin")


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace("boss@acme.test")
        self.ws.allowed_domains = {"acme.test"}
        self.ws.members["m@acme.test"] = {"role": "member", "totp_seed": "s"}
        self.ws.create_invite("live", "x@acme.test", "member", 10)

    def test_verify_code(self):
        self.assertTrue(verify_code(self.ws, "live"))
        self.ws.invites["live"]["used"] = True
        self.assertFalse(verify_code(self.ws, "live"))

    def test_unknown_code_is_refused(self):
        self.assertFalse(verify_code(self.ws, "nope"))

    def test_who_may_invite(self):
        self.assertTrue(may_invite(self.ws, "boss@acme.test"))
        self.assertFalse(may_invite(self.ws, "m@acme.test"))

    def test_stranger_may_not_invite(self):
        self.assertFalse(may_invite(self.ws, "stranger@evil.test"))

    def test_domain_allowlist(self):
        self.assertTrue(domain_ok(self.ws, "Ann@ACME.test"))
        self.assertFalse(domain_ok(self.ws, "ann@evil.test"))

    def test_address_without_domain_is_refused(self):
        self.assertFalse(domain_ok(self.ws, "nobody"))


class FormTests(unittest.TestCase):
    def test_email_is_normalised(self):
        self.assertEqual(check_email("  Ann@Acme.Test "), "ann@acme.test")

    def test_email_needs_an_at_sign(self):
        for bad in ("plain", "@acme.test", "ann@"):
            with self.assertRaises(ValueError):
                check_email(bad)

    def test_role_must_be_invitable(self):
        self.assertEqual(check_role("admin"), "admin")
        with self.assertRaises(ValueError):
            check_role("owner")

    def test_ttl_is_bounded(self):
        self.assertEqual(check_ttl(MAX_TTL_DAYS), MAX_TTL_DAYS)
        for bad in (0, MAX_TTL_DAYS + 1):
            with self.assertRaises(ValueError):
                check_ttl(bad)


class RenderTests(unittest.TestCase):
    def test_invite_description_hides_the_code(self):
        d = describe_invite("inv-7-abcd1234", {"email": "x@a.test", "role": "member", "expires": 9})
        self.assertEqual(d["email"], "x@a.test")
        self.assertNotIn("inv-7-abcd1234", repr(d))

    def test_member_row_hides_the_seed(self):
        row = member_row("x@a.test", {"role": "member", "totp_seed": "seed-x"})
        self.assertEqual(row["role"], "member")
        self.assertNotIn("seed-x", repr(row))

    def test_error_does_not_echo_the_code(self):
        msg = accept_error("inv-7-abcd1234", "expired")
        self.assertIn("expired", msg)
        self.assertNotIn("inv-7-abcd1234", msg)


class WindowTests(unittest.TestCase):
    def test_expiry_instant(self):
        inv = {"expires": 10}
        self.assertEqual([expired(inv, n) for n in (9, 10, 11)], [False, True, True])

    def test_reminder_starts_lead_days_before(self):
        inv = {"expires": 10}
        self.assertEqual([reminder_due(inv, d, 3) for d in (6, 7, 8)], [False, True, True])

    def test_batches_keep_the_tail(self):
        self.assertEqual(batches([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])


if __name__ == "__main__":
    unittest.main()
