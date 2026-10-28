import threading
import unittest

import limiter as limiter_module
from api import handle, headers_for
from keys import client_key, split_key
from limiter import RateLimiter
from stats import Stats


class Clock:
    def __init__(self, now=100.0):
        self.now = now

    def __call__(self):
        return self.now


class LimiterTests(unittest.TestCase):
    def test_exactly_limit_requests_are_allowed(self):
        lim = RateLimiter(limit=3, clock=Clock())
        self.assertEqual([lim.allow("a") for _ in range(5)], [True, True, True, False, False])

    def test_keys_are_independent(self):
        lim = RateLimiter(limit=1, clock=Clock())
        self.assertTrue(lim.allow("a"))
        self.assertTrue(lim.allow("b"))
        self.assertFalse(lim.allow("a"))

    def test_window_rolls_over(self):
        clock = Clock(100.0)
        lim = RateLimiter(limit=1, window=60, clock=clock)
        self.assertTrue(lim.allow("a"))
        self.assertFalse(lim.allow("a"))
        clock.now = 170.0
        self.assertTrue(lim.allow("a"))

    def test_api_returns_429_after_limit(self):
        lim = RateLimiter(limit=2, clock=Clock())
        codes = [handle(lim, "1.2.3.4", "/x")[0] for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    def test_concurrent_requests_cannot_exceed_limit(self):
        lim = RateLimiter(limit=1, clock=Clock())
        barrier = threading.Barrier(2, timeout=0.5)

        def hook():
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass

        results = []
        original = limiter_module._checkpoint
        limiter_module._checkpoint = hook
        try:
            threads = [threading.Thread(target=lambda: results.append(lim.allow("a")))
                       for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            limiter_module._checkpoint = original
        self.assertEqual(sum(results), 1)


class HelperTests(unittest.TestCase):
    def test_remaining_reset_and_headers(self):
        lim = RateLimiter(limit=3, clock=Clock())
        lim.allow("a")
        self.assertEqual(lim.remaining("a"), 2)
        self.assertEqual(headers_for(lim, "a"), {"X-RateLimit-Limit": "3", "X-RateLimit-Remaining": "2"})
        lim.reset("a")
        self.assertEqual(lim.remaining("a"), 3)
        self.assertEqual(lim.store.total(), 0)

    def test_client_keys(self):
        self.assertEqual(client_key("::FFFF:1.2.3.4"), "ip:1.2.3.4")
        self.assertEqual(client_key("1.2.3.4", user=" Ann "), "user:ann")
        self.assertEqual(split_key("user:ann"), ("user", "ann"))

    def test_stats(self):
        s = Stats()
        self.assertEqual(s.ratio_limited(), 0.0)
        for ok in (True, True, False, False):
            s.record(ok)
        self.assertEqual(s.summary(), "allowed=2 limited=2 ratio=0.50")


if __name__ == "__main__":
    unittest.main()
