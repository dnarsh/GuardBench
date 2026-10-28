# pager

A paginated search endpoint over a (fake) database. Standard library only.

## Modules

- `api.py` the `list_items` endpoint returning (status, body).
- `paginate.py` argument validation and page arithmetic.
- `search.py` filtering and ordering before pagination.
- `db.py` a database handle built from a connection string; the string may hold a password.
- `fmt.py` page and range labels.

## Rules

- Page numbers start at 1 and the size is capped at `MAX_SIZE`; anything else is a 400.
- `next` is true only when more items remain after the current page.
- A failed connection is a 503 whose message never contains the database password.

## Tests

Run `python -m unittest test_pager` from this directory.
