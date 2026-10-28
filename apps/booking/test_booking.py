import threading
import unittest

import booking as booking_module
from booking import Conflict, Scheduler
from fmt import agenda, fmt_slot, fmt_time
from rooms import Rooms
from slots import DAY, duration, merge_adjacent, overlaps, within_day


def scheduler():
    rooms = Rooms()
    rooms.add("blue", 4)
    rooms.add("red", 10)
    return Scheduler(rooms)


class SlotTests(unittest.TestCase):
    def test_overlap_is_half_open(self):
        self.assertTrue(overlaps(0, 60, 30, 90))
        self.assertTrue(overlaps(30, 40, 0, 60))
        self.assertFalse(overlaps(0, 60, 60, 120))
        self.assertFalse(overlaps(60, 120, 0, 60))
        self.assertTrue(overlaps(0, 60, 59, 61))

    def test_helpers(self):
        self.assertTrue(within_day(0, DAY))
        self.assertFalse(within_day(-1, 10))
        self.assertFalse(within_day(10, DAY + 1))
        self.assertFalse(within_day(10, 10))
        self.assertEqual(duration(60, 90), 30)
        self.assertEqual(merge_adjacent([(60, 90), (0, 30), (30, 60), (200, 210)]), [(0, 90), (200, 210)])


class SchedulerTests(unittest.TestCase):
    def test_booking_and_conflicts(self):
        s = scheduler()
        s.book("blue", 60, 120, "ann")
        with self.assertRaises(Conflict):
            s.book("blue", 90, 150, "bob")
        s.book("red", 90, 150, "bob")
        self.assertEqual(s.for_room("blue"), [(60, 120, "ann")])

    def test_back_to_back_bookings_are_allowed(self):
        s = scheduler()
        s.book("blue", 60, 120, "ann")
        s.book("blue", 120, 180, "bob")
        s.book("blue", 0, 60, "cy")
        self.assertEqual([w for _, _, w in s.for_room("blue")], ["cy", "ann", "bob"])

    def test_invalid_requests_are_rejected_and_book_nothing(self):
        s = scheduler()
        for start, end in ((60, 60), (90, 60), (0, -5)):
            with self.assertRaises(ValueError, msg=(start, end)):
                s.book("blue", start, end, "ann")
        with self.assertRaises(ValueError):
            s.book("green", 0, 60, "ann")
        self.assertEqual(s.bookings, [])

    def test_cancel_only_by_owner(self):
        s = scheduler()
        s.book("blue", 60, 120, "ann")
        self.assertFalse(s.cancel("blue", 60, "bob"))
        self.assertTrue(s.cancel("blue", 60, "ann"))
        self.assertEqual(s.bookings, [])

    def test_concurrent_requests_for_the_same_slot_have_one_winner(self):
        s = scheduler()
        barrier = threading.Barrier(2, timeout=0.5)

        def hook():
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass

        outcomes = []

        def attempt(who):
            try:
                s.book("blue", 60, 120, who)
                outcomes.append("ok")
            except Conflict:
                outcomes.append("conflict")

        original = booking_module._checkpoint
        booking_module._checkpoint = hook
        try:
            threads = [threading.Thread(target=attempt, args=(w,)) for w in ("ann", "bob")]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            booking_module._checkpoint = original
        self.assertEqual(sorted(outcomes), ["conflict", "ok"])
        self.assertEqual(len(s.bookings), 1)


class RoomAndFormatTests(unittest.TestCase):
    def test_rooms(self):
        rooms = Rooms()
        rooms.add("big", 12)
        rooms.add("small", 2)
        self.assertIn("big", rooms)
        self.assertEqual(rooms.capacity("small"), 2)
        self.assertEqual(rooms.names(), ["big", "small"])
        self.assertEqual(rooms.fitting(3), ["big"])
        self.assertEqual(rooms.fitting(1), ["small", "big"])
        with self.assertRaises(ValueError):
            rooms.add("none", 0)

    def test_formatting(self):
        self.assertEqual(fmt_time(570), "09:30")
        self.assertEqual(fmt_slot(540, 630), "09:00-10:30 (90 min)")
        self.assertEqual(agenda([(60, 120, "ann")]), ["01:00-02:00 (60 min) ann"])


if __name__ == "__main__":
    unittest.main()
