# wallet

A small bank: accounts, an append-only ledger, transfers with limits. Standard library only.

## Modules

- `accounts.py` the `Bank`: open, withdraw, transfer, history.
- `ledger.py` append-only entries; a balance is the sum of an account's entries.
- `limits.py` transfer and fee limits.
- `api.py` request layer returning (status, message).
- `statements.py` text statements; `fees.py` transfer fees.

## Rules

- A withdrawal never takes an account below zero, even with concurrent callers.
- Transfers must be positive and not above the limit; nothing moves when they are refused.
- The ledger is never edited, only appended to.

## Tests

Run `python -m unittest test_wallet` from this directory.
