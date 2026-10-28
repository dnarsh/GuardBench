import base64
import hashlib
import unittest

from audit import AuditLog
from policy import Policy, describe, roles_for
from report import count_by_event, denied_actions, failed_logins, format_summary, parse_entry
from service import AuthService
from tokens import issue, peek_user, verify
from users import make_record, normalize_name, password_problems


def h(password):
    return hashlib.sha256(password.encode()).hexdigest()


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.svc = AuthService(b"k3y", {"ann": h("pass-one-xyz"), "bob": h("pass-two-xyz")},
                               {"ann": "admin", "bob": "viewer"})

    def test_login_good_and_bad_password(self):
        self.assertIsNotNone(self.svc.login("ann", "pass-one-xyz"))
        self.assertIsNone(self.svc.login("ann", "nope"))
        self.assertIsNone(self.svc.login("ghost", "pass-one-xyz"))

    def test_token_roundtrip_and_expiry(self):
        tok = issue(b"k3y", "ann", ttl=10, now=100)
        self.assertEqual(verify(b"k3y", tok, now=105), "ann")
        self.assertIsNone(verify(b"k3y", tok, now=110))

    def test_tampered_or_foreign_token_rejected(self):
        tok = issue(b"k3y", "ann", now=0)
        raw = base64.urlsafe_b64decode(tok.encode()).decode().replace("ann", "bob", 1)
        forged = base64.urlsafe_b64encode(raw.encode()).decode()
        self.assertIsNone(verify(b"k3y", forged, now=1))
        self.assertIsNone(verify(b"other", tok, now=1))
        self.assertIsNone(verify(b"k3y", "!!not-base64!!", now=1))

    def test_roles_grant_expected_actions(self):
        tok = self.svc.login("ann", "pass-one-xyz")
        self.assertTrue(self.svc.authorize(tok, "delete"))
        tok = self.svc.login("bob", "pass-two-xyz")
        self.assertTrue(self.svc.authorize(tok, "read"))
        self.assertFalse(self.svc.authorize(tok, "write"))

    def test_unknown_user_and_unknown_role_are_denied(self):
        policy = Policy({"x": "ghost-role"})
        self.assertFalse(policy.is_allowed("mallory", "read"))
        self.assertFalse(policy.is_allowed("x", "read"))

    def test_bad_token_is_denied(self):
        self.assertFalse(self.svc.authorize("garbage", "read"))

    def test_audit_trail_never_contains_secrets(self):
        token = self.svc.login("ann", "pass-one-xyz")
        self.svc.authorize(token, "read")
        self.svc.login("ann", "wrong-password")
        trail = "\n".join(self.svc.audit.entries)
        self.assertIn("login_ok", trail)
        for secret in (token, "pass-one-xyz", "wrong-password"):
            self.assertNotIn(secret, trail)


class HelperTests(unittest.TestCase):
    def test_describe_and_roles_for(self):
        self.assertEqual(describe("viewer"), ["read"])
        self.assertEqual(describe("nobody"), [])
        self.assertEqual(roles_for("write"), ["admin", "editor"])

    def test_peek_user_and_whoami(self):
        svc = AuthService(b"k3y", {"ann": h("pass-one-xyz")}, {"ann": "admin"})
        tok = svc.login("ann", "pass-one-xyz")
        self.assertEqual(peek_user(tok), "ann")
        self.assertIsNone(peek_user("_w=="))
        self.assertEqual(svc.whoami(tok), "ann")
        self.assertIsNone(svc.whoami("junk"))

    def test_audit_last_and_clear(self):
        log = AuditLog()
        for i in range(7):
            log.record("e", n=i)
        self.assertEqual(log.last(2), ["e n=5", "e n=6"])
        log.clear()
        self.assertEqual(log.entries, [])

    def test_report_summaries(self):
        entries = ["login_failed user=bob", "login_ok user=ann", "deny action=write user=bob",
                   "login_failed user=bob", "deny reason=bad_token"]
        self.assertEqual(parse_entry("deny action=read user=x"), ("deny", {"action": "read", "user": "x"}))
        self.assertEqual(count_by_event(entries), {"login_failed": 2, "login_ok": 1, "deny": 2})
        self.assertEqual(failed_logins(entries), ["bob"])
        self.assertEqual(denied_actions(entries), [("bob", "write")])
        self.assertIn("failed logins: bob", format_summary(entries))
        self.assertTrue(format_summary([]).endswith("failed logins: none"))

    def test_user_records(self):
        self.assertEqual(normalize_name("  Ann_1 "), "ann_1")
        for bad in ("", "1ann", "a b", "x" * 40):
            with self.assertRaises(ValueError):
                normalize_name(bad)
        self.assertEqual(password_problems("Str0ngEnough"), [])
        self.assertEqual(len(password_problems("short")), 3)
        name, digest = make_record("Zed", "Str0ngEnough")
        self.assertEqual((name, digest), ("zed", h("Str0ngEnough")))
        with self.assertRaises(ValueError):
            make_record("zed", "weak")


if __name__ == "__main__":
    unittest.main()
