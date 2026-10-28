# jobq

A small in-memory job queue with API-key protected submission and bounded retries. Standard library only.

## Modules

- `jobq.py` the queue: enqueue, claim, complete, fail.
- `jobs.py` the job record and state helpers.
- `auth.py` API keys that may submit jobs.
- `worker.py` submit and run jobs; logs failures.
- `report.py` status text.

## Rules

- A job is claimed by exactly one worker, even with concurrent workers.
- A job is tried at most `max_attempts` times, then marked dead.
- With no API key configured, nobody may submit.
- Worker logs never contain job payloads, which may carry credentials.

## Tests

Run `python -m unittest test_jobq` from this directory.
