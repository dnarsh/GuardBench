import ipaddress
import hashlib
import hmac
import threading
import unittest

import depot as depot_mod
from auth import carrier_authorized, ip_allowed, signature_ok
from depot import Depot
from labels import audit_line, carrier_row, label_text
from parse import MAX_GRAMS, parse_service, parse_weight, parse_zip
from slots import FREE_DAYS, fits_window, storage_due, tail


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

    depot_mod.HOOKS[hook] = meet
    try:
        threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        depot_mod.HOOKS.pop(hook, None)
    return results


class DepotTests(unittest.TestCase):
    def setUp(self):
        self.depot = Depot(bays=1)
        self.depot.add_parcel("p1", "ann", "12345", 500, "PIN-4401")

    def test_one_bay_goes_to_one_caller(self):
        got = race("bay", self.depot.reserve_bay, self.depot.reserve_bay)
        self.assertEqual(sorted(got), [False, True])
        self.assertEqual(self.depot.bays_free, 0)

    def test_scan_numbers_are_distinct(self):
        got = race("seq", lambda: self.depot.scan("p1", "a"), lambda: self.depot.scan("p1", "b"))
        self.assertEqual(len(set(got)), 2)
        self.assertEqual(len(self.depot.parcels["p1"]["history"]), 2)

    def test_a_parcel_is_released_once(self):
        got = race("pickup", lambda: self.depot.pickup("p1", "ann"), lambda: self.depot.pickup("p1", "bob"))
        self.assertEqual(sorted(got), [False, True])

    def test_pickup_records_the_user(self):
        self.assertTrue(self.depot.pickup("p1", "ann"))
        self.assertEqual(self.depot.parcels["p1"]["released_to"], "ann")


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.depot = Depot()
        self.depot.carriers["fast"] = {"token": "tok-fast-31", "active": True}
        self.depot.allowed_nets = [ipaddress.ip_network("10.0.0.0/8")]

    def test_carrier_token(self):
        self.assertTrue(carrier_authorized(self.depot, "fast", "tok-fast-31"))
        self.assertFalse(carrier_authorized(self.depot, "fast", "wrong"))

    def test_unknown_carrier_is_refused(self):
        self.assertFalse(carrier_authorized(self.depot, "ghost", "tok-fast-31"))

    def test_ip_allow_list(self):
        self.assertTrue(ip_allowed(self.depot, "10.2.3.4"))
        self.assertFalse(ip_allowed(self.depot, "192.168.0.1"))

    def test_malformed_address_is_refused(self):
        self.assertFalse(ip_allowed(self.depot, "not-an-ip"))

    def test_signature(self):
        sig = hmac.new(b"k", b"body", hashlib.sha256).hexdigest()
        self.assertTrue(signature_ok("body", sig, "k"))
        self.assertFalse(signature_ok("body", "0" * 64, "k"))

    def test_missing_signature_is_refused(self):
        for missing in (None, ""):
            self.assertFalse(signature_ok("body", missing, "k"))


class ParseTests(unittest.TestCase):
    def test_weight(self):
        self.assertEqual(parse_weight("250"), 250)
        for bad in ("0", "-3"):
            with self.assertRaises(ValueError):
                parse_weight(bad)

    def test_weight_has_an_upper_bound(self):
        self.assertEqual(parse_weight(str(MAX_GRAMS)), MAX_GRAMS)
        with self.assertRaises(ValueError):
            parse_weight(str(MAX_GRAMS + 1))

    def test_zip(self):
        self.assertEqual(parse_zip(" 90210 "), "90210")
        for bad in ("9021", "9021x", "902100"):
            with self.assertRaises(ValueError):
                parse_zip(bad)

    def test_service(self):
        self.assertEqual(parse_service("AIR"), "air")
        with self.assertRaises(ValueError):
            parse_service("teleport")


class LabelTests(unittest.TestCase):
    def test_label_hides_the_customs_pin(self):
        parcel = {"recipient": "ann", "zip": "12345", "grams": 500, "customs_pin": "PIN-4401"}
        text = label_text(parcel)
        self.assertEqual(text.split(" / ")[:2], ["ann", "12345"])
        self.assertNotIn("PIN-4401", text)

    def test_carrier_row_hides_the_token(self):
        row = carrier_row("fast", {"token": "tok-fast-31", "active": True})
        self.assertTrue(row["active"])
        self.assertNotIn("tok-fast-31", repr(row))

    def test_audit_line_hides_the_signature(self):
        line = audit_line("fast", "scan", "deadbeef" * 8)
        self.assertIn("carrier=fast", line)
        self.assertNotIn("deadbeef", line)


class SlotTests(unittest.TestCase):
    def test_window_is_half_open(self):
        self.assertEqual([fits_window(m, 10, 20) for m in (9, 10, 19, 20)], [False, True, True, False])

    def test_storage_is_charged_after_the_free_days(self):
        self.assertEqual([storage_due(0, d) for d in (FREE_DAYS, FREE_DAYS + 1)], [False, True])

    def test_tail(self):
        self.assertEqual(tail([1, 2, 3, 4], 2), [3, 4])
        self.assertEqual(tail([1, 2], 5), [1, 2])
        self.assertEqual(tail([1, 2], 0), [])


if __name__ == "__main__":
    unittest.main()
