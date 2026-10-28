# inventory

Stock reservations, warehouse access and low-stock alerts. Standard library only.

## Modules

- `stock.py` levels and reservations.
- `access.py` which users may ship from which warehouse.
- `notify.py` alerts sent to a webhook with a bearer API key.
- `report.py` low-stock detection and level tables.

## Rules

- Stock never goes below zero, even with concurrent reservations.
- Users with no access entry may not ship from any warehouse.
- The webhook API key never appears in logs.

## Tests

Run `python -m unittest test_inventory` from this directory.
