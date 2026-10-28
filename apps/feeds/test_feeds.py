import threading
import unittest

import subs as subs_mod
from access import may_read, valid_unsub_token
from digest import fetch_error, item_line, subscriber_row
from inputs import MAX_ITEMS, check_feed_url, check_limit
from subs import Subs
from window import digest_slice, is_due, newest_first


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

    subs_mod.HOOKS[hook] = meet
    try:
        threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        subs_mod.HOOKS.pop(hook, None)
    return results


class SubsTests(unittest.TestCase):
    def setUp(self):
        self.s = Subs()

    def test_cap_holds_under_concurrency(self):
        self.s.subscribe("ann", "news")
        got = race("sub", lambda: self.s.subscribe("ann", "a"), lambda: self.s.subscribe("ann", "b"))
        self.assertEqual(sorted(got), [False, True])
        self.assertEqual(len(self.s.subscriptions["ann"]), 2)

    def test_an_item_is_delivered_once(self):
        got = race("seen", lambda: self.s.mark_seen("i1"), lambda: self.s.mark_seen("i1"))
        self.assertEqual(sorted(got), [False, True])

    def test_unsubscribe_and_listing(self):
        self.s.subscribe("ann", "b")
        self.s.subscribe("ann", "a")
        self.assertEqual(self.s.feeds_of("ann"), ["a", "b"])
        self.assertTrue(self.s.unsubscribe("ann", "a"))
        self.assertFalse(self.s.unsubscribe("ann", "a"))


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.s = Subs()
        self.s.add_feed("open", public=True)
        self.s.add_feed("club", public=False, members=["ann"])
        self.s.unsub_tokens["ann"] = "u-ann-5521"

    def test_read_access(self):
        self.assertTrue(may_read(self.s, "bob", "open"))
        self.assertTrue(may_read(self.s, "ann", "club"))
        self.assertFalse(may_read(self.s, "bob", "club"))

    def test_unknown_feed_is_refused(self):
        self.assertFalse(may_read(self.s, "ann", "ghost"))

    def test_unsubscribe_token(self):
        self.assertTrue(valid_unsub_token(self.s, "ann", "u-ann-5521"))
        self.assertFalse(valid_unsub_token(self.s, "ann", "u-ann-0000"))

    def test_unknown_user_cannot_unsubscribe(self):
        self.assertFalse(valid_unsub_token(self.s, "bob", "u-ann-5521"))


class InputTests(unittest.TestCase):
    def test_url_scheme(self):
        self.assertEqual(check_feed_url("https://x.test/rss"), "https://x.test/rss")
        for bad in ("file:///etc/passwd", "ftp://x.test/rss", "javascript:alert(1)"):
            with self.assertRaises(ValueError):
                check_feed_url(bad)

    def test_limit_is_bounded(self):
        self.assertEqual(check_limit(MAX_ITEMS), MAX_ITEMS)
        for bad in (0, MAX_ITEMS + 1):
            with self.assertRaises(ValueError):
                check_limit(bad)


class DigestTests(unittest.TestCase):
    def test_row_hides_the_token(self):
        row = subscriber_row("ann", {"feeds": ["a", "b"], "unsub_token": "u-ann-5521"})
        self.assertEqual(row["feeds"], 2)
        self.assertNotIn("u-ann-5521", repr(row))

    def test_fetch_error_drops_the_query_string(self):
        msg = fetch_error("https://x.test/rss?key=SECRET123", "timeout")
        self.assertIn("https://x.test/rss", msg)
        self.assertNotIn("SECRET123", msg)

    def test_item_line(self):
        self.assertEqual(item_line({"title": "Hi", "feed": "news"}), "- Hi (news)")


class WindowTests(unittest.TestCase):
    def test_slice_keeps_exactly_the_limit(self):
        self.assertEqual(digest_slice([1, 2, 3, 4], 2), [1, 2])
        self.assertEqual(digest_slice([1], 3), [1])

    def test_due_after_the_interval(self):
        self.assertEqual([is_due(0, n, 10) for n in (9, 10, 11)], [False, True, True])

    def test_newest_first(self):
        items = [{"day": 1}, {"day": 3}, {"day": 2}]
        self.assertEqual([i["day"] for i in newest_first(items)], [3, 2, 1])


if __name__ == "__main__":
    unittest.main()
