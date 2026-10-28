"""Fixed-window request counters kept in memory."""


class WindowStore:
    def __init__(self, window):
        self.window = window
        self._counts = {}

    def _bucket(self, key, now):
        return (key, int(now // self.window))

    def count(self, key, now):
        return self._counts.get(self._bucket(key, now), 0)

    def incr(self, key, now):
        bucket = self._bucket(key, now)
        self._counts[bucket] = self._counts.get(bucket, 0) + 1
        return self._counts[bucket]

    def prune(self, now):
        current = int(now // self.window)
        self._counts = {b: c for b, c in self._counts.items() if b[1] >= current}
