import threading
import unittest

import vault as vault_module
from acl import Acl
from names import is_valid_name, namespace, normalize
from secret import Secret, mask
from vault import AccessDenied, Vault, VersionConflict

VALUE = "s3cr3t-value-123"


def make():
    v = Vault(Acl({"db.password": ["ann"], "public.key": ["*"]}, admins=["root"]))
    v.set("db.password", VALUE)
    v.set("public.key", "pk-1")
    return v


class VaultTests(unittest.TestCase):
    def test_get_requires_a_grant(self):
        v = make()
        self.assertEqual(v.get("ann", "db.password"), VALUE)
        self.assertEqual(v.get("bob", "public.key"), "pk-1")
        self.assertEqual(v.get("root", "db.password"), VALUE)
        with self.assertRaises(AccessDenied):
            v.get("bob", "db.password")

    def test_unknown_secrets_are_denied_not_revealed_as_missing(self):
        v = make()
        with self.assertRaises(AccessDenied):
            v.get("bob", "no.such.secret")
        self.assertFalse(Acl({}).can_read("bob", "anything"))
        with self.assertRaises(KeyError):
            v.get("root", "no.such.secret")

    def test_names_are_validated_on_write(self):
        v = make()
        for bad in ("", "../etc/passwd", "Has Space", "UPPER", "1abc", "a" * 65, None, 5):
            with self.assertRaises(ValueError, msg=repr(bad)):
                v.set(bad, "x")
        v.set("ok.name-1_x", "x")

    def test_values_must_be_non_empty_strings(self):
        v = make()
        for bad in ("", None, 5, b"x"):
            with self.assertRaises(ValueError):
                v.set("good.name", bad)

    def test_versions_and_compare_and_set(self):
        v = make()
        self.assertEqual(v.set("db.password", "new-one"), 2)
        with self.assertRaises(VersionConflict):
            v.set("db.password", "x", expected_version=1)
        self.assertEqual(v.set("db.password", "x", expected_version=2), 3)
        self.assertEqual(v.set("fresh", "x", expected_version=0), 1)

    def test_nothing_secret_leaks_into_repr_errors_or_the_log(self):
        v = make()
        v.get("ann", "db.password")
        with self.assertRaises(AccessDenied) as ctx:
            v.get("bob", "db.password")
        seen = repr(Secret("db.password", VALUE)) + str(Secret("x", VALUE)) + str(ctx.exception)
        seen += "\n".join(v.log) + repr(v._items["db.password"])
        self.assertNotIn(VALUE, seen)

    def test_names_listing_delete_and_acl_editing(self):
        v = make()
        self.assertEqual(v.names("bob"), ["public.key"])
        self.assertEqual(v.names("ann"), ["db.password", "public.key"])
        v.acl.grant("db.password", "bob")
        self.assertEqual(v.acl.readers("db.password"), ["ann", "bob"])
        v.acl.revoke("db.password", "bob")
        self.assertEqual(v.acl.readers("db.password"), ["ann"])
        self.assertTrue(v.delete("public.key"))
        self.assertFalse(v.delete("public.key"))

    def test_concurrent_compare_and_set_has_one_winner(self):
        v = make()  # db.password is at version 1
        barrier = threading.Barrier(2, timeout=0.5)

        def hook():
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass

        outcomes = []

        def attempt(value):
            try:
                v.set("db.password", value, expected_version=1)
                outcomes.append("won")
            except VersionConflict:
                outcomes.append("lost")

        original = vault_module._checkpoint
        vault_module._checkpoint = hook
        try:
            threads = [threading.Thread(target=attempt, args=(x,)) for x in ("one", "two")]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            vault_module._checkpoint = original
        self.assertEqual(sorted(outcomes), ["lost", "won"])
        self.assertEqual(v._items["db.password"].version, 2)


class HelperTests(unittest.TestCase):
    def test_mask(self):
        self.assertEqual(mask("abcdef"), "******")
        self.assertEqual(mask("abcdef", keep=2), "****ef")
        self.assertEqual(mask("ab", keep=5), "**")

    def test_name_helpers(self):
        self.assertTrue(is_valid_name("a.b-c_d"))
        self.assertFalse(is_valid_name("a b"))
        self.assertEqual(namespace("db.password"), "db")
        self.assertEqual(namespace("solo"), "solo")
        self.assertEqual(normalize("  Db.Password "), "db.password")


if __name__ == "__main__":
    unittest.main()
