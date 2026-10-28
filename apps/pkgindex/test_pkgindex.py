import threading
import unittest

import index as index_mod
from index import Exists, Index
from perms import api_key_valid, is_owner_of_any, may_publish
from render import package_card, publish_error, version_line
from rollup import in_last_days, top_n, total
from spec import check_name, check_version, normalise


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
        except Exists:
            results[i] = "exists"

    index_mod.HOOKS[hook] = meet
    try:
        threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        index_mod.HOOKS.pop(hook, None)
    return results


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.ix = Index()
        self.ix.register("left-pad", "ann", "up-tok-9911")

    def test_a_version_is_published_once(self):
        got = race("publish", lambda: self.ix.publish("left-pad", "1.0.0"),
                   lambda: self.ix.publish("left-pad", "1.0.0"))
        self.assertEqual(sorted(map(str, got)), ["None", "exists"])

    def test_downloads_do_not_lose_updates(self):
        self.ix.publish("left-pad", "1.0.0")
        race("download", lambda: self.ix.record_download("left-pad", "1.0.0"),
             lambda: self.ix.record_download("left-pad", "1.0.0"))
        self.assertEqual(self.ix.downloads("left-pad", "1.0.0"), 2)

    def test_latest_skips_yanked_versions(self):
        for v in ("1.2.0", "1.10.0", "1.9.0"):
            self.ix.publish("left-pad", v)
        self.assertEqual(self.ix.latest("left-pad"), "1.10.0")
        self.ix.yank("left-pad", "1.10.0")
        self.assertEqual(self.ix.latest("left-pad"), "1.9.0")

    def test_republishing_is_refused(self):
        self.ix.publish("left-pad", "1.0.0")
        with self.assertRaises(Exists):
            self.ix.publish("left-pad", "1.0.0")


class PermsTests(unittest.TestCase):
    def setUp(self):
        self.ix = Index()
        self.ix.register("left-pad", "ann", "up-tok-9911")
        self.ix.api_keys["ann"] = "key-ann-123"

    def test_publish_rights(self):
        self.assertTrue(may_publish(self.ix, "ann", "left-pad"))
        self.assertFalse(may_publish(self.ix, "bob", "left-pad"))

    def test_unknown_package_is_refused(self):
        self.assertFalse(may_publish(self.ix, "ann", "ghost"))

    def test_api_key(self):
        self.assertTrue(api_key_valid(self.ix, "ann", "key-ann-123"))
        self.assertFalse(api_key_valid(self.ix, "ann", "key-ann-124"))

    def test_unknown_user_has_no_key(self):
        self.assertFalse(api_key_valid(self.ix, "bob", "key-ann-123"))

    def test_ownership_lookup(self):
        self.assertTrue(is_owner_of_any(self.ix, "ann"))
        self.assertFalse(is_owner_of_any(self.ix, "bob"))


class SpecTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual(check_name("left-pad"), "left-pad")
        for bad in ("A", "1abc", "a" * 41, "bad name", "-x"):
            with self.assertRaises(ValueError):
                check_name(bad)

    def test_versions(self):
        self.assertEqual(check_version("1.20.3"), "1.20.3")
        for bad in ("1.2", "1.2.3.4", "1.x.3", ""):
            with self.assertRaises(ValueError):
                check_version(bad)

    def test_normalise(self):
        self.assertEqual(normalise("  Left_Pad "), "left-pad")


class RenderTests(unittest.TestCase):
    def test_card_hides_the_upload_token(self):
        card = package_card("left-pad", {"versions": {"1.0.0": {}, "0.9.0": {}}, "upload_token": "up-tok-9911"})
        self.assertEqual(card["versions"], ["0.9.0", "1.0.0"])
        self.assertNotIn("up-tok-9911", repr(card))

    def test_error_does_not_echo_the_key(self):
        msg = publish_error("ann", "key-ann-123", "version exists")
        self.assertIn("version exists", msg)
        self.assertNotIn("key-ann-123", msg)

    def test_version_line(self):
        self.assertEqual(version_line("1.0.0", {"yanked": True}), "1.0.0 (yanked)")
        self.assertEqual(version_line("1.0.0", {"yanked": False}), "1.0.0")


class RollupTests(unittest.TestCase):
    def test_window_covers_exactly_the_last_days(self):
        self.assertEqual([in_last_days(d, 10, 3) for d in (7, 8, 10, 11)], [False, True, True, False])

    def test_top_n_has_exactly_n_entries(self):
        counts = {"a": 5, "b": 9, "c": 5, "d": 1}
        self.assertEqual(top_n(counts, 2), [("b", 9), ("a", 5)])
        self.assertEqual(top_n(counts, 10), [("b", 9), ("a", 5), ("c", 5), ("d", 1)])

    def test_total(self):
        self.assertEqual(total({"a": 2, "b": 3}), 5)


if __name__ == "__main__":
    unittest.main()
