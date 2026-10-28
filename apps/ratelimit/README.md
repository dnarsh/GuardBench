# ratelimit

Fixed-window request limiter with per-key counters, standard library only.

## Modules

- `limiter.py` the thread-safe `RateLimiter` (`allow`, `remaining`, `reset`).
- `store.py` in-memory counters keyed by (key, window number).
- `api.py` a tiny handler that answers 429 once the limit is used up.
- `keys.py` builds limiter keys from IPs and user names; `stats.py` counts outcomes.

## Rules

- Exactly `limit` requests per key and window are allowed, never more.
- The check and the count are one atomic step; concurrent callers cannot slip past.
- Keys are independent of each other.

## Tests

Run `python -m unittest test_ratelimit` from this directory.
