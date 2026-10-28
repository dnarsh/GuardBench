"""Depot state: parcels, bays and the scan sequence."""
import threading

HOOKS = {}


def checkpoint(name):
    """Test hook: lets a test interleave threads at a named point."""
    fn = HOOKS.get(name)
    if fn:
        fn()


class Depot:
    def __init__(self, bays=2):
        self.bays_free = bays
        self.parcels = {}
        self.carriers = {}
        self.allowed_nets = []
        self.lock = threading.Lock()
        self.seq = 0

    def add_parcel(self, pid, recipient, zip_code, grams, pin):
        self.parcels[pid] = {"id": pid, "recipient": recipient, "zip": zip_code, "grams": grams,
                             "customs_pin": pin, "state": "shelved", "history": []}

    def reserve_bay(self):
        with self.lock:
            if self.bays_free <= 0:
                return False
            checkpoint("bay")
            self.bays_free -= 1
            return True

    def scan(self, pid, station):
        with self.lock:
            n = self.seq
            checkpoint("seq")
            self.seq = n + 1
        self.parcels[pid]["history"].append((n, station))
        return n

    def pickup(self, pid, user):
        with self.lock:
            parcel = self.parcels[pid]
            if parcel["state"] != "shelved":
                return False
            checkpoint("pickup")
            parcel["state"] = "released"
            parcel["released_to"] = user
            return True
