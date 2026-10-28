"""Job records."""
import itertools

STATES = ("pending", "running", "done", "dead")
_ids = itertools.count(1)


class Job:
    def __init__(self, payload, max_attempts=3):
        self.id = next(_ids)
        self.payload = payload
        self.max_attempts = max_attempts
        self.attempts = 0
        self.state = "pending"
        self.error = None

    def __repr__(self):
        return "Job(%d, %s, attempts=%d)" % (self.id, self.state, self.attempts)


def summarize(jobs):
    """{state: count} for every known state, zeros included."""
    counts = dict.fromkeys(STATES, 0)
    for job in jobs:
        counts[job.state] += 1
    return counts


def by_state(jobs, state):
    """Jobs in the given state, oldest first."""
    return [job for job in jobs if job.state == state]
