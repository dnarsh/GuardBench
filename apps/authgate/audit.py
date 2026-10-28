"""In-memory audit trail."""


class AuditLog:
    def __init__(self):
        self.entries = []

    def record(self, event, **fields):
        parts = ["%s=%s" % kv for kv in sorted(fields.items())]
        line = " ".join([event] + parts)
        self.entries.append(line)
        return line

    def last(self, n=5):
        """The n most recent entries, oldest first."""
        return self.entries[-n:]

    def clear(self):
        self.entries = []
