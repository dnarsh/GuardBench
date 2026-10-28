# pkgindex

A tiny package index: owners, versions, yanking, download counts. Standard library only.

## Modules

- `index.py` the `Index`: register, publish, download counts, yank.
- `perms.py` publishing rights and API keys.
- `spec.py` validation of names and versions.
- `render.py` cards and messages.
- `rollup.py` download windows and rankings.

## Rules

- Unknown packages and unknown users are refused, never admitted.
- Names are lowercase, 2 to 40 characters; versions are three dot-separated numbers.
- A version is published once and download counts do not lose updates, even with concurrent callers.
- Upload tokens and API keys never appear in cards or messages.
- A window of `days` days covers today and the days before it; a ranking holds exactly `n` entries.

## Tests

Run `python -m unittest test_pkgindex` from this directory.
