import os
import tempfile
import unittest

from handlers import download, upload
from paths import safe_join
from quota import MAX_BYTES, MAX_FILES, QuotaError
from store import Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = self._tmp.name
        self.root = os.path.join(self.base, "store")
        self.store = Store(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_roundtrip(self):
        self.store.save("a.txt", b"hello")
        self.assertEqual(self.store.load("a.txt"), b"hello")

    def test_traversal_names_are_rejected(self):
        absolute = os.path.abspath(os.sep + "etc" + os.sep + "passwd")
        for name in ("../escape.txt", "sub/../../escape.txt", absolute, "", "a\x00b"):
            with self.assertRaises(ValueError, msg=name):
                self.store.save(name, b"x")
        self.assertFalse(os.path.exists(os.path.join(self.base, "escape.txt")))

    def test_sibling_directory_with_same_prefix_is_rejected(self):
        os.makedirs(os.path.join(self.base, "store2"))
        with self.assertRaises(ValueError):
            safe_join(self.root, "../store2/f.txt")

    def test_file_count_quota_is_exact(self):
        for i in range(MAX_FILES):
            self.store.save("f%d" % i, b"x")
        with self.assertRaises(QuotaError):
            self.store.save("one-too-many", b"x")
        self.assertEqual(len(self.store.names()), MAX_FILES)

    def test_size_limit_is_exact(self):
        self.store.save("ok", b"x" * MAX_BYTES)
        with self.assertRaises(QuotaError):
            self.store.save("big", b"x" * (MAX_BYTES + 1))

    def test_handlers_map_errors_to_status_codes(self):
        self.assertEqual(upload(self.store, "a", b"x")[0], 201)
        self.assertEqual(upload(self.store, "../a", b"x")[0], 400)
        self.assertEqual(upload(self.store, "b", b"x" * (MAX_BYTES + 1))[0], 413)
        self.assertEqual(download(self.store, "a"), (200, b"x"))
        self.assertEqual(download(self.store, "missing")[0], 404)
        self.assertEqual(download(self.store, "../a")[0], 400)


if __name__ == "__main__":
    unittest.main()
