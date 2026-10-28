"""Login and request authorisation."""
import hashlib

from audit import AuditLog
from policy import Policy
from tokens import issue, verify


class AuthService:
    def __init__(self, secret, users, assignments, audit=None):
        self.secret = secret
        self.users = dict(users)  # name -> sha256 hex of the password
        self.policy = Policy(assignments)
        self.audit = audit if audit is not None else AuditLog()

    def login(self, user, password):
        digest = hashlib.sha256(password.encode()).hexdigest()
        if self.users.get(user) != digest:
            self.audit.record("login_failed", user=user)
            return None
        token = issue(self.secret, user)
        self.audit.record("login_ok", user=user)
        return token

    def authorize(self, token, action):
        user = verify(self.secret, token)
        if user is None:
            self.audit.record("deny", reason="bad_token")
            return False
        allowed = self.policy.is_allowed(user, action)
        self.audit.record("allow" if allowed else "deny", user=user, action=action)
        return allowed
