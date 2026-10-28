import base64
import hashlib
import unittest

from policy import Policy
from service import AuthService
from tokens import issue, verify


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


if __name__ == "__main__":
    unittest.main()
