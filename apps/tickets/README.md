# tickets

A small help desk: tickets, agents with roles, assignment and service-level checks. Standard library only.

## Modules

- `core.py` the `Desk`: open, claim, close.
- `policy.py` authentication and permissions.
- `intake.py` validation of incoming data.
- `views.py` text and dict views.
- `paging.py` pages and overdue windows.

## Rules

- Unknown agents and unknown keys are refused, never admitted.
- Titles are 1 to 120 characters, priorities are low, normal or high; assignees must be agents.
- Ticket ids are unique and a ticket is claimed by one agent only, even with concurrent callers.
- Agent keys never appear in views or messages.
- Pages are 1-based; a ticket is overdue once its age reaches the service-level days.

## Tests

Run `python -m unittest test_tickets` from this directory.
