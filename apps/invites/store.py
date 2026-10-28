"""Workspace state: members, invites and seats."""
import hashlib
import threading

HOOKS = {}


def checkpoint(name):
    """Test hook: lets a test interleave threads at a named point."""
    fn = HOOKS.get(name)
    if fn:
        fn()


class SeatsFull(Exception):
    pass


class Workspace:
    def __init__(self, owner, seats=3, secret="ws-secret"):
        self.owner = owner
        self.seats = seats
        self.secret = secret
        self.members = {owner: {"role": "owner", "totp_seed": "seed-" + owner}}
        self.invites = {}
        self.allowed_domains = set()
        self.lock = threading.Lock()
        self.counter = 1

    def issue_code(self):
        with self.lock:
            n = self.counter
            checkpoint("issue")
            self.counter = n + 1
        tag = hashlib.sha256(("%s:%d" % (self.secret, n)).encode()).hexdigest()[:8]
        return "inv-%d-%s" % (n, tag)

    def create_invite(self, code, email, role, expires):
        self.invites[code] = {"email": email, "role": role, "expires": expires, "used": False}

    def add_member(self, email, role):
        with self.lock:
            if len(self.members) >= self.seats:
                raise SeatsFull(email)
            checkpoint("seat")
            self.members[email] = {"role": role, "totp_seed": "seed-" + email}

    def accept(self, code, email):
        with self.lock:
            invite = self.invites[code]
            if invite["used"]:
                return False
            checkpoint("accept")
            invite["used"] = True
        self.add_member(email, invite["role"])
        return True
