import threading
import unittest

import core
from core import Desk
from intake import MAX_TITLE, check_assignee, check_new
from paging import overdue, page, page_count
from policy import authenticate, can_close, can_view
from views import agent_summary, login_failed, ticket_line


def race(hook, *calls):
    """Run calls in threads that meet at the named hook; return their results."""
    barrier = threading.Barrier(len(calls), timeout=0.3)

    def meet():
        try:
            barrier.wait()
        except threading.BrokenBarrierError:
            pass

    results = [None] * len(calls)

    def run(i, fn):
        results[i] = fn()

    core.HOOKS[hook] = meet
    try:
        threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        core.HOOKS.pop(hook, None)
    return results


class DeskTests(unittest.TestCase):
    def setUp(self):
        self.desk = Desk()
        self.desk.add_agent("ann", "agent", "k-ann-1")
        self.desk.add_agent("root", "admin", "k-root-9")

    def test_ids_are_unique_under_concurrency(self):
        ids = race("open", lambda: self.desk.open_ticket("a", "", "u"),
                   lambda: self.desk.open_ticket("b", "", "u"))
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual(len(self.desk.tickets), 2)

    def test_only_one_agent_can_claim(self):
        tid = self.desk.open_ticket("a", "", "u")
        got = race("claim", lambda: self.desk.claim(tid, "ann"), lambda: self.desk.claim(tid, "root"))
        self.assertEqual(sorted(got), [False, True])

    def test_close_and_open_list(self):
        tid = self.desk.open_ticket("a", "", "u")
        self.desk.close(tid)
        self.assertEqual(self.desk.all_open(), [])


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.desk = Desk()
        self.desk.add_agent("ann", "agent", "k-ann-1")
        self.desk.add_agent("root", "admin", "k-root-9")
        self.ticket = {"assignee": "ann", "author": "u"}

    def test_authenticate(self):
        self.assertTrue(authenticate(self.desk, "ann", "k-ann-1"))
        self.assertFalse(authenticate(self.desk, "ann", "nope"))

    def test_unknown_agent_cannot_authenticate(self):
        self.assertFalse(authenticate(self.desk, "ghost", "k-ann-1"))

    def test_close_permissions(self):
        self.assertTrue(can_close(self.desk, "root", self.ticket))
        self.assertTrue(can_close(self.desk, "ann", self.ticket))
        self.assertFalse(can_close(self.desk, "ann", {"assignee": "root"}))

    def test_unknown_user_cannot_close(self):
        self.assertFalse(can_close(self.desk, "ghost", self.ticket))

    def test_view_rules(self):
        self.assertTrue(can_view(self.desk, "u", self.ticket))
        self.assertTrue(can_view(self.desk, "ann", self.ticket))
        self.assertFalse(can_view(self.desk, "stranger", self.ticket))


class IntakeTests(unittest.TestCase):
    def test_good_ticket(self):
        self.assertEqual(check_new("  Printer  ", None, "high"), ("Printer", "", "high"))

    def test_title_required(self):
        for bad in ("", "   ", None):
            with self.assertRaises(ValueError):
                check_new(bad, "", "low")

    def test_title_is_bounded(self):
        check_new("x" * MAX_TITLE, "", "low")
        with self.assertRaises(ValueError):
            check_new("x" * (MAX_TITLE + 1), "", "low")

    def test_priority_must_be_known(self):
        with self.assertRaises(ValueError):
            check_new("t", "", "urgent")

    def test_assignee_must_be_an_agent(self):
        desk = Desk()
        desk.add_agent("ann", "agent", "k")
        self.assertEqual(check_assignee(desk, "ann"), "ann")
        with self.assertRaises(ValueError):
            check_assignee(desk, "bob")


class ViewTests(unittest.TestCase):
    def test_summary_hides_key(self):
        desk = Desk()
        desk.add_agent("ann", "agent", "k-secret-77")
        s = agent_summary(desk, "ann")
        self.assertEqual((s["name"], s["role"]), ("ann", "agent"))
        self.assertNotIn("k-secret-77", repr(s))

    def test_login_failure_does_not_echo_key(self):
        msg = login_failed("ann", "k-guess-55")
        self.assertIn("ann", msg)
        self.assertNotIn("k-guess-55", msg)

    def test_ticket_line(self):
        self.assertEqual(ticket_line({"id": 3, "priority": "low", "title": "T"}), "#3 [low] T")


class PagingTests(unittest.TestCase):
    def test_pages_are_one_based(self):
        items = list(range(10))
        self.assertEqual(page(items, 1, 4), [0, 1, 2, 3])
        self.assertEqual(page(items, 3, 4), [8, 9])

    def test_overdue_at_the_boundary(self):
        ts = [{"id": 1, "opened": 0}, {"id": 2, "opened": 2}]
        self.assertEqual([t["id"] for t in overdue(ts, 3, 3)], [1])

    def test_page_count(self):
        self.assertEqual([page_count(n, 5) for n in (0, 5, 6, 10)], [0, 1, 2, 2])


if __name__ == "__main__":
    unittest.main()
