"""Usage meter: per-account storage use against a limit, plus invoice numbers."""
import threading

HOOKS = {}


def checkpoint(name):
    """Test hook: lets a test interleave threads at a named point."""
    fn = HOOKS.get(name)
    if fn:
        fn()


class QuotaExceeded(Exception):
    pass


class Meter:
    def __init__(self):
        self.accounts = {}
        self.staff = {}
        self.lock = threading.Lock()
        self.invoice_no = 1000

    def add_account(self, name, plan, limit, card_token):
        self.accounts[name] = {"plan": plan, "limit": limit, "used": 0, "card_token": card_token}

    def reserve(self, name, nbytes):
        with self.lock:
            acct = self.accounts[name]
            if acct["used"] + nbytes > acct["limit"]:
                raise QuotaExceeded(name)
            checkpoint("reserve")
            acct["used"] += nbytes

    def usage(self, name):
        acct = self.accounts[name]
        return "%d of %d bytes" % (acct["used"], acct["limit"])

    def headroom(self, name):
        acct = self.accounts[name]
        return acct["limit"] - acct["used"]

    def release(self, name, nbytes):
        acct = self.accounts[name]
        acct["used"] = max(0, acct["used"] - nbytes)

    def next_invoice(self):
        with self.lock:
            n = self.invoice_no
            checkpoint("invoice")
            self.invoice_no = n + 1
        return n
