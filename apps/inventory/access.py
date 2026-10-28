"""Which users may ship from which warehouse."""


class Access:
    def __init__(self, config):
        self.config = {user: set(houses) for user, houses in config.items()}

    def can_ship_from(self, user, warehouse):
        """True when user may ship from warehouse ('*' grants every warehouse)."""
        allowed = self.config.get(user)
        if allowed is None:
            return False  # users without an entry get nothing
        return warehouse in allowed or "*" in allowed

    def warehouses_for(self, user):
        """Warehouses the user is listed for, sorted."""
        return sorted(self.config.get(user, ()))

    def add_user(self, user, houses):
        self.config[user] = set(houses)
