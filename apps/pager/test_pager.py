import unittest

from api import list_items
from db import ConnectError, Database, redact
from fmt import page_label, range_label
from paginate import MAX_SIZE, has_next, page_count, page_slice, validate_args
from search import ALLOWED_SORT, matches, names, search

DSN = "pg://svc:hunter2-pw@db.internal/shop"


def rows(n):
    return [{"name": "item%03d" % i, "price": n - i} for i in range(n)]


class PaginateTests(unittest.TestCase):
    def test_arguments_are_validated(self):
        self.assertEqual(validate_args(1, 20), (1, 20))
        self.assertEqual(validate_args(3, MAX_SIZE), (3, MAX_SIZE))
        for page, size in ((0, 10), (-1, 10), (1, 0), (1, -5), (1, MAX_SIZE + 1), (1, 10 ** 6),
                           ("1", 10), (1, None), (True, 10), (1.5, 10)):
            with self.assertRaises(ValueError, msg=(page, size)):
                validate_args(page, size)

    def test_slices_cover_every_item_exactly_once(self):
        items = list(range(45))
        pages = [page_slice(items, p, 20) for p in (1, 2, 3, 4)]
        self.assertEqual([len(p) for p in pages], [20, 20, 5, 0])
        self.assertEqual(sum(pages, []), items)

    def test_counts_and_next_flag_at_the_boundaries(self):
        self.assertEqual([page_count(t, 20) for t in (0, 1, 20, 21, 40)], [0, 1, 1, 2, 2])
        self.assertTrue(has_next(41, 2, 20))
        self.assertFalse(has_next(40, 2, 20))
        self.assertFalse(has_next(0, 1, 20))
        self.assertTrue(has_next(21, 1, 20))
        self.assertFalse(has_next(20, 1, 20))


class SearchTests(unittest.TestCase):
    def test_filter_and_order(self):
        items = [{"name": "Banana", "price": 3}, {"name": "apple", "price": 5}, {"name": "Cherry", "price": 1}]
        self.assertEqual(names(search(items, "AN")), ["Banana"])
        self.assertEqual(names(search(items, "", "price")), ["Cherry", "Banana", "apple"])
        self.assertEqual(names(search(items, "", "price", descending=True)), ["apple", "Banana", "Cherry"])
        self.assertTrue(matches(items[0], ""))
        self.assertEqual(ALLOWED_SORT, ("name", "price"))
        with self.assertRaises(ValueError):
            search(items, "", "password")


class ApiTests(unittest.TestCase):
    def test_paged_listing(self):
        db = Database(DSN, rows(45))
        status, body = list_items(db, page=3, size=20)
        self.assertEqual((status, len(body["items"]), body["pages"], body["next"]), (200, 5, 3, False))
        status, body = list_items(db, page=2, size=20)
        self.assertTrue(body["next"] and body["items"][0] == "item020")

    def test_bad_input_is_a_400(self):
        db = Database(DSN, rows(5))
        self.assertEqual(list_items(db, page=0)[0], 400)
        self.assertEqual(list_items(db, size=MAX_SIZE + 1)[0], 400)

    def test_connection_errors_do_not_leak_the_password(self):
        db = Database(DSN, up=False)
        status, body = list_items(db)
        self.assertEqual(status, 503)
        self.assertNotIn("hunter2-pw", body["error"])
        self.assertNotIn("hunter2-pw", repr(db))
        with self.assertRaises(ConnectError) as ctx:
            db.connect()
        self.assertNotIn("hunter2-pw", str(ctx.exception))

    def test_redact(self):
        self.assertEqual(redact(DSN), "pg://svc:***@db.internal/shop")
        self.assertEqual(redact("pg://db.internal/shop"), "pg://db.internal/shop")


class FormatTests(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(page_label(2, 5), "page 2 of 5")
        self.assertEqual(page_label(1, 0), "no results")
        self.assertEqual(range_label(2, 20, 95), "21-40 of 95")
        self.assertEqual(range_label(5, 20, 95), "81-95 of 95")
        self.assertEqual(range_label(1, 20, 0), "0 of 0")
        self.assertEqual(range_label(9, 20, 95), "0 of 95")


if __name__ == "__main__":
    unittest.main()
