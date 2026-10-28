# uploadstore

A flat, quota-limited file store for user uploads, standard library only.

## Modules

- `store.py` saves, loads, deletes and lists files under one root directory.
- `paths.py` resolves user supplied names safely inside the root.
- `quota.py` limits the number of files and the size of each file.
- `handlers.py` maps store errors to HTTP-style status codes.
- `names.py` makes display names safe; `report.py` formats usage.

## Rules

- A name that would leave the storage root is rejected before anything is written.
- Exactly `MAX_FILES` files and `MAX_BYTES` bytes per file are allowed, one more is not.
- Errors map to 400 (bad name), 404 (missing), 413 (quota).

## Tests

Run `python -m unittest test_uploadstore` from this directory.
