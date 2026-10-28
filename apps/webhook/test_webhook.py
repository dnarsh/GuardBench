import unittest

from config import load_secret, load_tolerance
from events import event_type, is_known, summarize
from handler import describe_status, handle
from retry import delay, schedule
from signature import compute, header_name, strip_prefix, verify

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


class HelperTests(unittest.TestCase):
    def test_signature_helpers(self):
        self.assertEqual(header_name(), "x-signature")
        self.assertEqual(strip_prefix("sha256=abc"), "abc")
        self.assertEqual(strip_prefix("abc"), "abc")

    def test_status_phrases_and_tolerance(self):
        self.assertEqual(describe_status(401), "Unauthorized")
        self.assertEqual(describe_status(999), "Unknown")
        self.assertEqual(load_tolerance({}), 300)
        self.assertEqual(load_tolerance({"WEBHOOK_TOLERANCE": "60"}), 60)
        self.assertEqual(load_tolerance({"WEBHOOK_TOLERANCE": "-5"}), 300)
        self.assertEqual(load_tolerance({"WEBHOOK_TOLERANCE": "0"}), 300)

    def test_events(self):
        self.assertEqual(event_type({"type": "push"}), "push")
        self.assertEqual(event_type([1]), "unknown")
        self.assertTrue(is_known("ping") and not is_known("nope"))
        self.assertEqual(summarize({"type": "ping", "a": 1}), "ping (2 fields)")
        self.assertEqual(summarize("x"), "unknown (0 fields)")

    def test_retry_schedule(self):
        self.assertEqual(schedule(4), [2, 4, 8, 16])
        self.assertEqual(delay(20), 300)
        with self.assertRaises(ValueError):
            delay(0)


if __name__ == "__main__":
    unittest.main()
