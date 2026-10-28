"""Counters of allowed and limited requests."""


class Stats:
    def __init__(self):
        self.allowed = 0
        self.limited = 0

    def record(self, ok):
        if ok:
            self.allowed += 1
        else:
            self.limited += 1

    def ratio_limited(self):
        """Share of requests that were limited; 0.0 before any request."""
        seen = self.allowed + self.limited
        if seen == 0:
            return 0.0
        return self.limited / seen

    def summary(self):
        return "allowed=%d limited=%d ratio=%.2f" % (self.allowed, self.limited, self.ratio_limited())
