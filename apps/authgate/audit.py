"""In-memory audit trail."""


class AuditLog:
    def __init__(self):
        self.entries = []

    def record(self, event, **fields):
        parts = ["%s=%s" % kv for kv in sorted(fields.items())]
        line = " ".join([event] + parts)
        self.entries.append(line)
        return line
