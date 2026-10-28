"""A fake database handle built from a connection string."""
from urllib.parse import urlsplit


class ConnectError(Exception):
    pass


def redact(dsn):
    """'pg://user:pw@host/db' -> 'pg://user:***@host/db'."""
    parts = urlsplit(dsn)
    if parts.password is None:
        return dsn
    netloc = parts.netloc.replace(":" + parts.password + "@", ":***@")
    return parts._replace(netloc=netloc).geturl()


class Database:
    def __init__(self, dsn, rows=(), up=True):
        self.dsn = dsn
        self.up = up
        self.rows = list(rows)

    def connect(self):
        """Return self, or raise ConnectError when the server is down."""
        if not self.up:
            raise ConnectError("cannot connect to %s" % redact(self.dsn))
        return self

    def __repr__(self):
        return "Database(%s)" % redact(self.dsn)
