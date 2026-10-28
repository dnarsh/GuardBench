"""In-memory session records."""


class SessionStore:
    def __init__(self):
        self._rows = {}

    def put(self, sid, user, expires):
        self._rows[sid] = (user, expires)

    def get(self, sid):
        return self._rows.get(sid)

    def delete(self, sid):
        self._rows.pop(sid, None)

    def count_for(self, user, now):
        """Live sessions of the user at time now."""
        return sum(1 for u, exp in self._rows.values() if u == user and exp > now)

    def purge(self, now):
        """Drop expired rows; returns how many were removed."""
        dead = [sid for sid, (_, exp) in self._rows.items() if exp <= now]
        for sid in dead:
            del self._rows[sid]
        return len(dead)

    def users(self):
        """Names of users that have at least one row, sorted."""
        return sorted({u for u, _ in self._rows.values()})

    def drop_user(self, user):
        """Remove every row of the user; returns how many were removed."""
        mine = [sid for sid, (u, _) in self._rows.items() if u == user]
        for sid in mine:
            del self._rows[sid]
        return len(mine)
