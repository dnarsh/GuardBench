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


def describe(role):
    """Sorted action names a role grants; empty for unknown roles."""
    return sorted(ROLES.get(role, ()))


def roles_for(action):
    """Roles that grant the action, sorted."""
    return sorted(role for role, actions in ROLES.items() if action in actions)
