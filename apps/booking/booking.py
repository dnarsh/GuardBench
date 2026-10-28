"""Room bookings without double booking."""
import threading

from slots import overlaps


def _checkpoint():
    """No-op hook between the conflict scan and the insert; tests interleave threads here."""


class Conflict(Exception):
    pass


class Scheduler:
    def __init__(self, rooms):
        self.rooms = rooms
        self.bookings = []  # (room, start, end, who)
        self._lock = threading.Lock()

    def book(self, room, start, end, who):
        """Reserve [start, end) in room; Conflict when any minute is already taken."""
        if room not in self.rooms:
            raise ValueError("unknown room")
        if end <= start:
            raise ValueError("end must be after start")
        with self._lock:
            for r, s, e, _ in self.bookings:
                if r == room and overlaps(start, end, s, e):
                    raise Conflict(room)
            _checkpoint()
            self.bookings.append((room, start, end, who))

    def cancel(self, room, start, who):
        """Remove a booking by its owner; True when one was removed."""
        with self._lock:
            for item in self.bookings:
                if item[0] == room and item[1] == start and item[3] == who:
                    self.bookings.remove(item)
                    return True
        return False

    def for_room(self, room):
        """(start, end, who) for the room, ordered by start."""
        return sorted((s, e, w) for r, s, e, w in self.bookings if r == room)
