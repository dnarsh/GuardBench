"""Submit and run jobs."""


def submit(queue, auth, key, payload):
    """Return (status, body): 202 with the job id, or 401."""
    if not auth.check(key):
        return 401, "unauthorized"
    job = queue.enqueue(payload)
    return 202, str(job.id)


def run_job(queue, job, handler, log):
    """Run handler(payload); on failure record it and log a line without the payload."""
    try:
        handler(job.payload)
    except Exception as exc:  # the handler is user code
        queue.fail(job, str(exc))
        log.append("job %d failed: %s" % (job.id, exc))
        return False
    queue.complete(job)
    log.append("job %d done" % job.id)
    return True


def drain(queue, handler, log):
    """Claim and run jobs until none is pending; returns how many runs happened."""
    ran = 0
    while True:
        job = queue.claim()
        if job is None:
            return ran
        run_job(queue, job, handler, log)
        ran += 1
