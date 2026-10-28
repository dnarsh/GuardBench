import difflib
import os

import pytest

from guardbench.defects import Defect
from guardbench.validate import validate_defect

MOD = "def is_ok(x):\n    if x < 0:\n        return False\n    return True\n"
TEST = ("import unittest\nfrom mod import is_ok\n\n\nclass T(unittest.TestCase):\n"
        "    def test_neg(self):\n        self.assertFalse(is_ok(-1))\n"
        "    def test_pos(self):\n        self.assertTrue(is_ok(1))\n\n\n"
        "if __name__ == '__main__':\n    unittest.main()\n")


def diff(old, new, path="mod.py"):
    return "".join(difflib.unified_diff(
        old.splitlines(True), new.splitlines(True), "a/" + path, "b/" + path))


BUG = diff(MOD, MOD.replace("return False", "return True"))
CLEAN = diff(MOD, MOD.replace("x < 0", "not x >= 0"))


@pytest.fixture
def make(tmp_path):
    def _make(mod=MOD, test=TEST, bug=BUG, clean=CLEAN, start=3, end=3, test_module="test_mod"):
        app = tmp_path / "app"
        app.mkdir(exist_ok=True)
        (app / "mod.py").write_text(mod, newline="\n")
        (app / "test_mod.py").write_text(test, newline="\n")
        return Defect("d", "app", "fail-open", test_module, "mod.py", start, end, bug, clean, str(app))
    return _make


def test_valid_defect_has_no_problems(make):
    assert validate_defect(make(), timeout=30) == []


def test_defect_whose_test_does_not_fail_is_rejected(make):
    # same behaviour change but the test never exercises it
    weak = TEST.replace("self.assertFalse(is_ok(-1))", "self.assertTrue(is_ok(1))")
    probs = validate_defect(make(test=weak), timeout=30)
    assert any("bug patch" in p and "did not fail" in p for p in probs)


def test_clean_twin_that_fails_is_rejected(make):
    probs = validate_defect(make(clean=BUG), timeout=30)
    assert any("clean twin" in p for p in probs)


def test_failing_clean_app_is_rejected(make):
    probs = validate_defect(make(mod=MOD.replace("return True", "return False")), timeout=30)
    assert any("clean app" in p for p in probs)


def test_unapplicable_patch_is_rejected(make):
    probs = validate_defect(make(bug=BUG.replace("x < 0", "x < 99")), timeout=30)
    assert any("bug patch" in p for p in probs)


def test_timeout_is_reported_and_not_a_proof(make):
    slow = TEST.replace("def test_pos(self):\n", "def test_pos(self):\n        import time; time.sleep(30)\n")
    probs = validate_defect(make(test=slow), timeout=1)
    assert any("timed out" in p for p in probs)


def test_timeout_on_bug_version_does_not_count_as_failure(make):
    hang = MOD.replace("return True", "import time; time.sleep(30); return True")
    bug = diff(MOD, hang)
    probs = validate_defect(make(bug=bug, start=4, end=4), timeout=2)
    assert any("bug patch" in p and "timed out" in p for p in probs)


def test_patch_touching_the_test_file_is_rejected(make):
    bug = diff(TEST, TEST.replace("assertFalse", "assertTrue"), "test_mod.py")
    probs = validate_defect(make(bug=bug, start=7, end=7), timeout=30)
    assert any("test module" in p for p in probs)


def test_patch_with_path_traversal_is_rejected(make, tmp_path):
    (tmp_path / "victim.py").write_text("x\n")
    evil = "--- a/../victim.py\n+++ b/../victim.py\n@@ -1 +1 @@\n-x\n+y\n"
    probs = validate_defect(make(bug=evil), timeout=30)
    assert probs and (tmp_path / "victim.py").read_text() == "x\n"


def test_location_must_overlap_the_patch(make):
    probs = validate_defect(make(start=1, end=1), timeout=30)
    assert any("location" in p for p in probs)


def test_location_beyond_file_is_rejected(make):
    probs = validate_defect(make(start=40, end=41), timeout=30)
    assert any("location" in p for p in probs)


def test_environment_is_scrubbed(make, monkeypatch):
    monkeypatch.setenv("GB_SECRET_TOKEN", "hunter2")
    leaky = TEST.replace("def test_pos(self):\n",
                         "def test_pos(self):\n        import os; self.assertNotIn('GB_SECRET_TOKEN', os.environ)\n")
    assert validate_defect(make(test=leaky), timeout=30) == []


def test_runs_in_a_copy_and_leaves_the_app_untouched(make):
    d = make()
    before = open(os.path.join(d.app_dir, "mod.py")).read()
    validate_defect(d, timeout=30)
    assert open(os.path.join(d.app_dir, "mod.py")).read() == before


def test_symlink_in_app_is_rejected(make, tmp_path):
    d = make()
    try:
        os.symlink(str(tmp_path / "victim.py"), os.path.join(d.app_dir, "link.py"))
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    assert any("symlink" in p for p in validate_defect(d, timeout=30))


def test_missing_test_module_is_not_a_pass_or_a_proof(make):
    probs = validate_defect(make(test_module="test_nope"), timeout=30)
    assert probs
