# invites

Workspace membership by invite code: seats, roles, expiring single-use invites. Standard library only.

## Modules

- `store.py` the `Workspace`: codes, seats, accepting an invite.
- `access.py` who may invite, valid codes, allowed address domains.
- `forms.py` validation of invite requests.
- `render.py` rows and messages for people.
- `window.py` expiry, reminders and batching.

## Rules

- Unknown or used codes, unknown actors and malformed addresses are refused, never admitted.
- Emails need an `@`, roles are member or admin, lifetimes are 1 to 30 days.
- A code is accepted once and the seat limit holds even with concurrent callers; issued codes are distinct.
- Invite codes and second-factor seeds never appear in rows or messages.
- An invite is expired at its expiry instant; reminders start `lead` days before it.

## Tests

Run `python -m unittest test_invites` from this directory.
