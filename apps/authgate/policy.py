"""Role based access policy."""

ROLES = {
    "admin": {"read", "write", "delete"},
    "editor": {"read", "write"},
    "viewer": {"read"},
}


class Policy:
    def __init__(self, assignments):
        self.assignments = dict(assignments)

    def is_allowed(self, user, action):
        """True only when the user's role grants the action."""
        try:
            role = self.assignments[user]
            return action in ROLES[role]
        except KeyError:
            return False
