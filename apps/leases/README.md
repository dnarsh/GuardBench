# leases

Named leases with fence tokens, renewal windows and expiry. Standard library only.

## Modules

- `table.py` the `LeaseTable`: acquire, renew, release.
- `guard.py` holder and fence-token checks.
- `config.py` validation of names and lifetimes.
- `report.py` operator rows and messages.
- `clock.py` expiry arithmetic.

## Rules

- Unknown leases, wrong holders and malformed tokens are refused, never admitted.
- Names are lowercase and at most 64 characters; lifetimes are 1 to 3600 seconds.
- A lease is granted to one caller and fences are distinct, even with concurrent callers.
- Fence tokens never appear in rows or messages.
- A lease is expired at its expiry instant; renewal is allowed once `margin` seconds or fewer remain.

## Tests

Run `python -m unittest test_leases` from this directory.
