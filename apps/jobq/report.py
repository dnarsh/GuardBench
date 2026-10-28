"""Queue status text."""
from jobs import STATES, summarize


def status_line(jobs):
    """'pending=1 running=0 done=2 dead=0'."""
    counts = summarize(jobs)
    return " ".join("%s=%d" % (state, counts[state]) for state in STATES)


def failure_report(jobs):
    """One line per dead job with its last error, oldest first."""
    lines = []
    for job in jobs:
        if job.state == "dead":
            lines.append("job %d: %s" % (job.id, job.error or "unknown error"))
    return lines
