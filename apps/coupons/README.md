# coupons

Signed discount codes with expiry and use limits. Standard library only.

## Modules

- `codes.py` signs and checks coupon codes (`BASE-<tag>`).
- `service.py` the catalog and `redeem`.
- `rules.py` discount arithmetic in whole cents.
- `report.py` listings for the admin page.

## Rules

- Only codes carrying a valid tag are redeemable; with no signing secret nothing is.
- A coupon works through its expiry second and stops right after.
- A coupon with `max_uses` of N redeems exactly N times.
- Percentages must be between 1 and 100.
- Error messages never reveal the expected tag or the secret.

## Tests

Run `python -m unittest test_coupons` from this directory.
