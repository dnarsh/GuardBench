"""Ticket desk state: tickets, agents and the shared lock."""
import threading

HOOKS = {}


def checkpoint(name):
    """Test hook: lets a test interleave threads at a named point."""
    fn = HOOKS.get(name)
    if fn:
        fn()


class Desk:
    def __init__(self):
        self.tickets = {}
        self.agents = {}
        self.api_keys = {}
        self.lock = threading.Lock()
        self.next_id = 1

    def add_agent(self, name, role, api_key):
        self.agents[name] = role
        self.api_keys[name] = api_key

    def open_ticket(self, title, body, author, priority="normal", day=0):
        with self.lock:
            tid = self.next_id
            checkpoint("open")
            self.next_id = tid + 1
            self.tickets[tid] = {"id": tid, "title": title, "body": body, "author": author,
                                 "priority": priority, "opened": day, "status": "open",
                                 "assignee": None}
        return tid

    def claim(self, tid, agent):
        with self.lock:
            ticket = self.tickets[tid]
            if ticket["assignee"] is not None:
                return False
            checkpoint("claim")
            ticket["assignee"] = agent
            return True

    def close(self, tid):
        self.tickets[tid]["status"] = "closed"

    def all_open(self):
        return [t for t in self.tickets.values() if t["status"] == "open"]
