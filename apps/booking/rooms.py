"""Bookable rooms."""


class Rooms:
    def __init__(self):
        self._capacity = {}

    def add(self, name, capacity):
        """Register a room; capacity is the number of seats."""
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._capacity[name] = capacity

    def __contains__(self, name):
        return name in self._capacity

    def capacity(self, name):
        return self._capacity[name]

    def names(self):
        """Room names, sorted."""
        return sorted(self._capacity)

    def fitting(self, people):
        """Rooms with at least `people` seats, smallest first."""
        fits = [n for n, c in self._capacity.items() if c >= people]
        return sorted(fits, key=lambda n: (self._capacity[n], n))
