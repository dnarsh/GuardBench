# feeds

Feed subscriptions and digests: per-user caps, delivery de-duplication, unsubscribe tokens. Standard library only.

## Modules

- `subs.py` the `Subs` table: subscribe, mark items seen, unsubscribe.
- `access.py` read access and unsubscribe-token checks.
- `inputs.py` validation of URLs and limits.
- `digest.py` digest text and operator rows.
- `window.py` digest sizes and send intervals.

## Rules

- Unknown feeds and unknown users are refused, never admitted.
- Feed URLs are http or https; digest limits are 1 to 50.
- A subscription cap and first delivery of an item hold even with concurrent callers.
- Unsubscribe tokens and URL query strings never appear in rows or messages.
- A digest holds at most `limit` items; one is due once the interval has fully elapsed.

## Tests

Run `python -m unittest test_feeds` from this directory.
