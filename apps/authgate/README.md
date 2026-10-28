# authgate

Token login and role based authorisation, standard library only.

## Modules

- `tokens.py` signs and verifies session tokens (HMAC-SHA256, expiry).
- `policy.py` maps users to roles and roles to actions.
- `service.py` ties them together: `login` and `authorize`.
- `audit.py` keeps an in-memory trail of events; it must never hold secrets.
- `report.py` summarises the trail; `users.py` validates user records.

## Rules

- Unknown users, unknown roles and bad tokens are denied.
- Passwords and tokens never appear in the audit trail.
- Tokens expire; the expiry is part of the signed payload.

## Tests

Run `python -m unittest test_authgate` from this directory.
