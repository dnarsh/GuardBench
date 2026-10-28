import threading
import unittest

import manager as manager_module
from fmt import describe, humanize_ttl, mask_sid
from manager import MAX_TTL, MIN_TTL, SessionLimit, SessionManager
from policy import BackendError, BlockList
from store import SessionStore


class Clock:
    def __init__(self, now=1000):
        self.now = now

    def __call__(self):
        return self.now


def make(policy=None, max_per_user=2, clock=None):
    clock = clock or Clock()
    return SessionManager(SessionStore(), policy or BlockList(), clock, ttl=600,
                          max_per_user=max_per_user), clock


class SessionTests(unittest.TestCase):
    def test_create_and_validate(self):
        mgr, _ = make()
        sid = mgr.create("ann")
        self.assertEqual(mgr.validate(sid), "ann")
        self.assertIsNone(mgr.validate("nope"))

    def test_session_is_valid_until_the_expiry_second_exactly(self):
        mgr, clock = make()
        sid = mgr.create("ann")  # expires at 1600
        clock.now = 1599
        self.assertEqual(mgr.validate(sid), "ann")
        clock.now = 1600
        self.assertIsNone(mgr.validate(sid))

    def test_lifetime_must_be_in_range(self):
        mgr, _ = make()
        for bad in (0, MIN_TTL - 1, MAX_TTL + 1, -5):
            with self.assertRaises(ValueError, msg=bad):
                mgr.create("ann", ttl=bad)
        mgr.create("ann", ttl=MIN_TTL)
        mgr.create("bob", ttl=MAX_TTL)

    def test_user_must_be_a_non_empty_string(self):
        mgr, _ = make()
        for bad in ("", "  ", None, 5):
            with self.assertRaises(ValueError):
                mgr.create(bad)

    def test_per_user_limit_counts_only_live_sessions(self):
        mgr, clock = make(max_per_user=2)
        mgr.create("ann")
        mgr.create("ann")
        with self.assertRaises(SessionLimit):
            mgr.create("ann")
        mgr.create("bob")
        clock.now += 601
        mgr.create("ann")

    def test_blocked_users_and_unreachable_block_list_are_refused(self):
        policy = BlockList(blocked=["eve"])
        mgr, _ = make(policy)
        sid_eve, sid_ann = mgr.create("eve"), mgr.create("ann")
        self.assertIsNone(mgr.validate(sid_eve))
        self.assertEqual(mgr.validate(sid_ann), "ann")

        def down(user):
            raise BackendError("unreachable")

        policy.backend = down
        self.assertIsNone(mgr.validate(sid_ann))

    def test_block_unblock_and_revoke(self):
        policy = BlockList()
        mgr, _ = make(policy)
        sid = mgr.create("ann")
        policy.block("ann")
        self.assertEqual(policy.size(), 1)
        self.assertIsNone(mgr.validate(sid))
        policy.unblock("ann")
        self.assertEqual(mgr.validate(sid), "ann")
        self.assertEqual(mgr.revoke_all("ann"), 1)
        self.assertIsNone(mgr.validate(sid))

    def test_store_purge_and_users(self):
        mgr, clock = make()
        mgr.create("bob")
        mgr.create("ann")
        self.assertEqual(mgr.store.users(), ["ann", "bob"])
        clock.now += 10000
        self.assertEqual(mgr.store.purge(clock()), 2)
        self.assertEqual(mgr.store.users(), [])

    def test_concurrent_creates_cannot_exceed_the_limit(self):
        mgr, _ = make(max_per_user=1)
        barrier = threading.Barrier(2, timeout=0.5)

        def hook():
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass

        results = []

        def attempt():
            try:
                mgr.create("ann")
                results.append("ok")
            except SessionLimit:
                results.append("limit")

        original = manager_module._checkpoint
        manager_module._checkpoint = hook
        try:
            threads = [threading.Thread(target=attempt) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            manager_module._checkpoint = original
        self.assertEqual(sorted(results), ["limit", "ok"])


class FormatTests(unittest.TestCase):
    def test_humanize_mask_and_describe(self):
        self.assertEqual([humanize_ttl(s) for s in (5, 60, 300, 3900, 7200)], ["5s", "1m", "5m", "1h 5m", "2h 0m"])
        self.assertEqual(mask_sid("abcdef123"), "abcd...")
        self.assertEqual(mask_sid("abc"), "abc")
        self.assertEqual(describe("ann", 1300, 1000), "ann expires in 5m")
        self.assertEqual(describe("ann", 1000, 1000), "ann expired")


if __name__ == "__main__":
    unittest.main()
