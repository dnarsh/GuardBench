"""Who may read which secret."""


class Acl:
    def __init__(self, rules=None, admins=()):
        self.rules = {name: set(users) for name, users in (rules or {}).items()}
        self.admins = set(admins)

    def can_read(self, user, name):
        """True when user may read the secret `name`."""
        if user in self.admins:
            return True
        allowed = self.rules.get(name)
        if allowed is None:
            return False  # unknown secrets are not readable
        return user in allowed or "*" in allowed

    def grant(self, name, user):
        self.rules.setdefault(name, set()).add(user)

    def revoke(self, name, user):
        self.rules.get(name, set()).discard(user)

    def readers(self, name):
        """Users granted `name`, sorted (admins are not listed)."""
        return sorted(self.rules.get(name, ()))
