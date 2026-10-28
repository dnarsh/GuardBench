# sessions

Session store with expiry, per-user limits and a block list. Standard library only.

## Modules

- `manager.py` creates and validates sessions.
- `store.py` keeps session rows in memory.
- `policy.py` the block list consulted on every validation.
- `fmt.py` text helpers for listings.

## Rules

- A session is valid strictly before its expiry time and not after.
- A user may hold at most `max_per_user` live sessions, even under concurrent requests.
- If the block list cannot be reached, the session is refused.
- Lifetimes outside `MIN_TTL`..`MAX_TTL` are rejected.

## Tests

Run `python -m unittest test_sessions` from this directory.
