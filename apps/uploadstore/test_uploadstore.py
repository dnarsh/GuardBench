import os
import tempfile
import unittest

from handlers import download, listing, remove, upload
from names import display_name, unique_name
from paths import extension, is_hidden, safe_join
from quota import MAX_BYTES, MAX_FILES, QuotaError, bytes_left, describe_limits
from report import is_full, percent_full, usage_line
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


class HelperTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = Store(os.path.join(self._tmp.name, "s"))

    def tearDown(self):
        self._tmp.cleanup()

    def test_quota_helpers(self):
        self.assertIn(str(MAX_FILES), describe_limits())
        self.assertEqual(bytes_left(10, 100), 90)
        self.assertEqual(bytes_left(500, 100), 0)

    def test_path_helpers(self):
        self.assertEqual(extension("dir/Photo.JPG"), ".jpg")
        self.assertEqual(extension(".bashrc"), "")
        self.assertTrue(is_hidden("a/.secret/b"))
        self.assertFalse(is_hidden("a/b"))

    def test_delete_usage_listing_and_remove(self):
        self.store.save("a", b"xx")
        self.store.save("b", b"yyy")
        self.assertEqual(self.store.usage(), (2, 5))
        self.assertEqual(listing(self.store), (200, "a\nb"))
        self.assertEqual(remove(self.store, "a"), (204, ""))
        self.assertEqual(remove(self.store, "a")[0], 404)
        self.assertEqual(remove(self.store, "../a")[0], 400)
        self.assertEqual(self.store.names(), ["b"])

    def test_names(self):
        self.assertEqual(display_name("my file<1>.txt"), "my_file_1_.txt")
        self.assertEqual(display_name("???"), "unnamed")
        self.assertEqual(len(display_name("x" * 100, limit=20)), 19)
        self.assertEqual(unique_name("a.txt", {"a.txt"}), "a-2.txt")
        self.assertEqual(unique_name("a.txt", {"a.txt", "a-2.txt"}), "a-3.txt")
        self.assertEqual(unique_name("b", set()), "b")

    def test_report(self):
        self.assertEqual(usage_line(1, 10), "1/%d files, 10/%d bytes" % (MAX_FILES, MAX_FILES * MAX_BYTES))
        self.assertEqual(percent_full(MAX_FILES), 100)
        self.assertTrue(is_full(MAX_FILES) and not is_full(MAX_FILES - 1))


if __name__ == "__main__":
    unittest.main()
