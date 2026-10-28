import threading
import unittest

import stock as stock_module
from access import Access
from notify import Notifier
from report import alert_low, levels_table, low_stock
from stock import OutOfStock, Stock

KEY = "whk-live-0123456789"


def stocked():
    s = Stock()
    s.add("bolt", 10)
    s.add("nut", 2)
    return s


class StockTests(unittest.TestCase):
    def test_reserve_and_exhaust(self):
        s = stocked()
        s.reserve("bolt", 10)
        self.assertEqual(s.available("bolt"), 0)
        with self.assertRaises(OutOfStock):
            s.reserve("bolt", 1)
        with self.assertRaises(OutOfStock):
            s.reserve("ghost", 1)

    def test_add_validates_and_skus_are_sorted(self):
        s = stocked()
        with self.assertRaises(ValueError):
            s.add("bolt", 0)
        self.assertEqual(s.skus(), ["bolt", "nut"])

    def test_concurrent_reservations_cannot_oversell(self):
        s = Stock()
        s.add("last", 1)
        barrier = threading.Barrier(2, timeout=0.5)

        def hook():
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass

        outcomes = []

        def attempt():
            try:
                s.reserve("last", 1)
                outcomes.append("ok")
            except OutOfStock:
                outcomes.append("out")

        original = stock_module._checkpoint
        stock_module._checkpoint = hook
        try:
            threads = [threading.Thread(target=attempt) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            stock_module._checkpoint = original
        self.assertEqual(sorted(outcomes), ["ok", "out"])
        self.assertEqual(s.available("last"), 0)


class AccessTests(unittest.TestCase):
    def test_access_rules(self):
        acc = Access({"ann": ["north"], "root": ["*"]})
        self.assertTrue(acc.can_ship_from("ann", "north"))
        self.assertFalse(acc.can_ship_from("ann", "south"))
        self.assertTrue(acc.can_ship_from("root", "anywhere"))

    def test_unlisted_users_get_nothing(self):
        acc = Access({"ann": ["north"]})
        self.assertFalse(acc.can_ship_from("mallory", "north"))
        self.assertFalse(Access({}).can_ship_from("anyone", "any"))

    def test_listing_and_editing(self):
        acc = Access({"ann": ["south", "north"]})
        self.assertEqual(acc.warehouses_for("ann"), ["north", "south"])
        self.assertEqual(acc.warehouses_for("zed"), [])
        acc.add_user("zed", ["east"])
        self.assertTrue(acc.can_ship_from("zed", "east"))


class NotifyTests(unittest.TestCase):
    def test_alert_sends_with_the_key_but_never_logs_it(self):
        sent = []
        n = Notifier("https://hooks.example/stock", KEY, sender=lambda u, h, b: sent.append((u, h, b)))
        text = n.alert("nut", 2)
        self.assertEqual(text, "low stock: nut has 2 left")
        self.assertEqual(sent[0][1]["Authorization"], "Bearer " + KEY)
        self.assertNotIn(KEY, "\n".join(n.log))
        self.assertIn("nut", n.log[0])

    def test_alerting_without_a_sender_only_logs(self):
        n = Notifier("https://hooks.example/stock", KEY)
        n.alert("nut", 1)
        self.assertEqual(len(n.log), 1)


class ReportTests(unittest.TestCase):
    def test_low_stock_alerts_and_table(self):
        s = stocked()
        n = Notifier("https://hooks.example/stock", KEY)
        self.assertEqual(low_stock(s, 2), ["nut"])
        self.assertEqual(alert_low(s, n, 5), 1)
        self.assertEqual(alert_low(s, n, 10), 2)
        self.assertEqual(levels_table(s), ["bolt          10", "nut            2"])


if __name__ == "__main__":
    unittest.main()
