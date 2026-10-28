import unittest

from config import load_secret
from handler import handle
from signature import compute, verify

SECRET = b"whsec-unit-test-secret"
BODY = b'{"type": "ping"}'


def signed(body=BODY, secret=SECRET):
    return {"X-Signature": compute(secret, body)}


class WebhookTests(unittest.TestCase):
    def test_valid_signature_is_accepted(self):
        self.assertEqual(handle(SECRET, signed(), BODY), (200, "received ping"))

    def test_header_name_is_case_insensitive(self):
        self.assertTrue(verify(SECRET, {"x-SIGNATURE": compute(SECRET, BODY)}, BODY))

    def test_missing_signature_is_rejected(self):
        self.assertEqual(handle(SECRET, {}, BODY)[0], 401)
        self.assertFalse(verify(SECRET, {"Other": "x"}, BODY))

    def test_wrong_signature_is_rejected(self):
        self.assertEqual(handle(SECRET, signed(secret=b"other"), BODY)[0], 401)
        self.assertEqual(handle(SECRET, signed(body=b"{}"), BODY)[0], 401)

    def test_rejection_does_not_reveal_the_expected_signature(self):
        status, text = handle(SECRET, {"X-Signature": "sha256=00"}, BODY)
        self.assertEqual(status, 401)
        self.assertNotIn(compute(SECRET, BODY), text)
        self.assertNotIn(SECRET.decode(), text)

    def test_unset_secret_fails_closed(self):
        self.assertEqual(handle(b"", signed(secret=b""), BODY)[0], 500)

    def test_signed_garbage_is_a_400(self):
        body = b"not json"
        self.assertEqual(handle(SECRET, signed(body), body)[0], 400)

    def test_load_secret(self):
        self.assertEqual(load_secret({"WEBHOOK_SECRET": "abc"}), b"abc")
        self.assertEqual(load_secret({}), b"")


if __name__ == "__main__":
    unittest.main()
