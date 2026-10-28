# links

Share links for files: download limits, viewer lists, optional passwords, expiry. Standard library only.

## Modules

- `registry.py` the `Registry`: create, open, add viewers, revoke.
- `gate.py` password and ownership decisions.
- `fields.py` validation of link settings.
- `views.py` summaries, log lines and error text.
- `windows.py` staleness, paging bounds and size buckets.

## Rules

- Unknown or revoked links, failed hashing and unknown owners are refused, never admitted.
- Names have no path separators and no leading dot; expiry is 1 to 90 days; download limits are positive integers.
- Tokens are unique, a download limit and a viewer cap hold even with concurrent callers.
- Password hashes and full tokens never appear in summaries, log lines or messages.
- A link is stale after more than its idle days; page bounds never exceed the total; 1 KiB is already medium.

## Tests

Run `python -m unittest test_links` from this directory.
