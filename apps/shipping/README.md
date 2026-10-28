# shipping

A parcel depot: shelving, bay reservation, scan history, carrier authentication. Standard library only.

## Modules

- `depot.py` the `Depot`: bays, scans, pickup.
- `auth.py` carrier tokens, network allow-list, body signatures.
- `parse.py` parsing of weight, postcode and service.
- `labels.py` label text, carrier rows and audit lines.
- `slots.py` windows, storage fees and history tails.

## Rules

- Unknown carriers, malformed addresses and missing signatures are refused, never admitted.
- Weights are 1 to 30000 g, postcodes are five digits, services are ground, air or freight.
- A bay is reserved once, scan numbers are distinct and a parcel is released once, even with concurrent callers.
- Carrier tokens, customs pins and signatures never appear on labels, rows or audit lines.
- A window includes its start and excludes its end; storage is charged after five free days.

## Tests

Run `python -m unittest test_shipping` from this directory.
