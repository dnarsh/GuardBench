"""FIFO job queue with claim, complete and retry."""
import threading

from jobs import Job


def _checkpoint():
    """No-op hook between finding a pending job and marking it running; tests interleave here."""


class JobQueue:
    def __init__(self):
        self.jobs = []
        self._lock = threading.Lock()

    def enqueue(self, payload, max_attempts=3):
        """Add a pending job and return it."""
        job = Job(payload, max_attempts)
        with self._lock:
            self.jobs.append(job)
        return job

    def claim(self):
        """Mark the oldest pending job running and return it, or None."""
        with self._lock:
            for job in self.jobs:
                if job.state == "pending":
                    _checkpoint()
                    job.state = "running"
                    job.attempts += 1
                    return job
        return None

    def complete(self, job):
        job.state = "done"
        job.error = None

    def fail(self, job, error):
        """Record a failure: retry until max_attempts tries are used, then give up."""
        job.error = error
        job.state = "dead" if job.attempts >= job.max_attempts else "pending"

    def pending_count(self):
        return sum(1 for job in self.jobs if job.state == "pending")
