# vault

Versioned secret store with per-secret access control. Standard library only.

## Modules

- `vault.py` the `Vault`: set (with compare-and-set), get, names, delete.
- `acl.py` which users may read which secret.
- `secret.py` the `Secret` wrapper that never prints its value.
- `names.py` secret name rules.

## Rules

- Only valid names are stored; anything else is rejected before it is used.
- Secrets nobody was granted are unreadable, and unknown names look the same as denied ones.
- Concurrent compare-and-set writes with the same expected version: exactly one wins.
- No secret value appears in `repr`, `str`, error messages or the vault log.

## Tests

Run `python -m unittest test_vault` from this directory.
