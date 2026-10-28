# booking

Room scheduling that never double books. Standard library only.

## Modules

- `booking.py` the `Scheduler`: book, cancel, list.
- `slots.py` slot arithmetic in minutes since midnight.
- `rooms.py` the room registry with capacities.
- `fmt.py` text for schedules.

## Rules

- A slot is half open: it includes its start minute and excludes its end minute, so a booking
  may start exactly when another ends.
- A slot must end after it starts and the room must exist.
- Two concurrent requests for the same room and time: exactly one succeeds.

## Tests

Run `python -m unittest test_booking` from this directory.
