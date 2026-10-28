import threading
import unittest

import jobq as jobq_module
from auth import KeyAuth
from jobq import JobQueue
from jobs import by_state, summarize
from report import failure_report, status_line
from worker import drain, run_job, submit


class QueueTests(unittest.TestCase):
    def test_fifo_claim_and_complete(self):
        q = JobQueue()
        a, b = q.enqueue("a"), q.enqueue("b")
        self.assertIs(q.claim(), a)
        self.assertEqual((a.state, a.attempts), ("running", 1))
        q.complete(a)
        self.assertIs(q.claim(), b)
        self.assertIsNone(q.claim())
        self.assertEqual(q.pending_count(), 0)

    def test_a_job_is_tried_exactly_max_attempts_times(self):
        q = JobQueue()
        job = q.enqueue("x", max_attempts=2)
        q.claim()
        q.fail(job, "boom")
        self.assertEqual(job.state, "pending")
        q.claim()
        q.fail(job, "boom")
        self.assertEqual(job.state, "dead")
        self.assertIsNone(q.claim())

    def test_one_job_cannot_be_claimed_twice_concurrently(self):
        q = JobQueue()
        q.enqueue("only")
        barrier = threading.Barrier(2, timeout=0.5)

        def hook():
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass

        got = []
        original = jobq_module._checkpoint
        jobq_module._checkpoint = hook
        try:
            threads = [threading.Thread(target=lambda: got.append(q.claim())) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            jobq_module._checkpoint = original
        self.assertEqual(len([j for j in got if j is not None]), 1)


class AuthTests(unittest.TestCase):
    def test_keys(self):
        auth = KeyAuth(["k-1"])
        self.assertTrue(auth.check("k-1"))
        self.assertFalse(auth.check("k-2"))
        self.assertFalse(auth.check(None))
        auth.add("k-2")
        auth.add("k-2")
        self.assertEqual(auth.count(), 2)
        self.assertTrue(auth.check("k-2"))

    def test_no_configured_keys_means_nobody_gets_in(self):
        for keys in ((), ("",), (None,)):
            auth = KeyAuth(keys)
            self.assertFalse(auth.check("anything"))
            self.assertFalse(auth.check(""))


class WorkerTests(unittest.TestCase):
    def test_submit_status_codes(self):
        q, auth = JobQueue(), KeyAuth(["k"])
        self.assertEqual(submit(q, auth, "k", {"n": 1})[0], 202)
        self.assertEqual(submit(q, auth, "nope", {"n": 1}), (401, "unauthorized"))
        self.assertEqual(len(q.jobs), 1)
        self.assertEqual(submit(q, KeyAuth(), "k", {})[0], 401)

    def test_drain_runs_retries_until_dead(self):
        q, log = JobQueue(), []
        q.enqueue("ok")
        bad = q.enqueue("bad", max_attempts=2)

        def handler(payload):
            if payload == "bad":
                raise RuntimeError("cannot process")

        self.assertEqual(drain(q, handler, log), 3)
        self.assertEqual(bad.state, "dead")
        self.assertEqual(status_line(q.jobs), "pending=0 running=0 done=1 dead=1")
        self.assertEqual(failure_report(q.jobs), ["job %d: cannot process" % bad.id])

    def test_failure_logs_never_contain_the_payload(self):
        q, log = JobQueue(), []
        job = q.enqueue({"api_token": "tok-123-secret", "to": "ann"})

        def handler(payload):
            raise ValueError("delivery failed")

        q.claim()
        self.assertFalse(run_job(q, job, handler, log))
        self.assertIn("delivery failed", log[0])
        self.assertNotIn("tok-123-secret", "\n".join(log))
        self.assertNotIn("ann", "\n".join(log))

    def test_job_helpers(self):
        q = JobQueue()
        a = q.enqueue(1)
        q.enqueue(2)
        q.claim()
        self.assertEqual(summarize(q.jobs), {"pending": 1, "running": 1, "done": 0, "dead": 0})
        self.assertEqual(by_state(q.jobs, "running"), [a])
        self.assertIn("running", repr(a))


if __name__ == "__main__":
    unittest.main()
