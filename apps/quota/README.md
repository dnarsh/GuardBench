# quota

Storage quotas and billing: per-account limits, plans and features, invoices, cycle arithmetic. Standard library only.

## Modules

- `meter.py` the `Meter`: reserve and release space, invoice numbers.
- `authz.py` who may adjust accounts, which features a plan has.
- `plans.py` plans and validation of sizes.
- `invoice.py` invoice rows and messages.
- `cycle.py` billing-cycle arithmetic.

## Rules

- Unknown staff and unknown accounts are refused, never admitted.
- Plans are free, pro or team; sizes are non-negative integers.
- Usage never exceeds the limit and invoice numbers are distinct, even with concurrent callers.
- Card tokens and full card numbers never appear in rows or messages.
- A cycle of `length` days includes its first day and not the day after its last; the current day counts as remaining.

## Tests

Run `python -m unittest test_quota` from this directory.
