import os
import tempfile
import unittest

import pytest

from guardbench import patch
from guardbench.patch import PatchError

SRC = "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\n"

MODIFY = """--- a/m.py
+++ b/m.py
@@ -1,5 +1,5 @@
 a = 1
 b = 2
-c = 3
+c = 30
 d = 4
 e = 5
"""

DELETE = """--- a/m.py
+++ b/m.py
@@ -1,5 +1,4 @@
 a = 1
 b = 2
-c = 3
 d = 4
 e = 5
"""


def hdr(path):
    return "--- a/%s\n+++ b/%s\n@@ -1,1 +1,1 @@\n-x\n+y\n" % (path, path)


@pytest.fixture
def root(tmp_path):
    (tmp_path / "m.py").write_text(SRC, newline="\n")
    return tmp_path


def test_apply_modifies_file(root):
    patch.apply(str(root), MODIFY)
    assert (root / "m.py").read_text() == SRC.replace("c = 3", "c = 30")


def test_apply_deletion(root):
    patch.apply(str(root), DELETE)
    assert (root / "m.py").read_text() == "a = 1\nb = 2\nd = 4\ne = 5\n"


def test_context_mismatch_rejected_and_file_untouched(root):
    bad = MODIFY.replace(" b = 2", " b = 99")
    with pytest.raises(PatchError, match="context"):
        patch.apply(str(root), bad)
    assert (root / "m.py").read_text() == SRC


@pytest.mark.parametrize("path", [
    "../evil.py", "a/../../evil.py", "/etc/passwd", "C:/x.py", "x\\y.py",
    "", "dir//x.py", "./x.py", "x\x00.py",
])
def test_unsafe_paths_rejected(root, path):
    with pytest.raises(PatchError):
        patch.parse(hdr(path))


def test_traversal_never_writes_outside(tmp_path):
    inner = tmp_path / "inner"
    inner.mkdir()
    (tmp_path / "victim.py").write_text("x\n")
    with pytest.raises(PatchError):
        patch.apply(str(inner), hdr("../victim.py"))
    assert (tmp_path / "victim.py").read_text() == "x\n"


def test_symlink_escape_rejected(tmp_path):
    inner = tmp_path / "inner"
    inner.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("x\n")
    try:
        os.symlink(str(outside), str(inner / "link.py"))
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(PatchError, match="escapes"):
        patch.apply(str(inner), hdr("link.py"))
    assert outside.read_text() == "x\n"


def test_missing_file_rejected(root):
    with pytest.raises(PatchError, match="no such file"):
        patch.apply(str(root), hdr("nope.py"))


def test_rename_rejected():
    with pytest.raises(PatchError, match="rename"):
        patch.parse("--- a/x.py\n+++ b/y.py\n@@ -1 +1 @@\n-a\n+b\n")


def test_missing_prefix_rejected():
    with pytest.raises(PatchError):
        patch.parse("--- x.py\n+++ x.py\n@@ -1 +1 @@\n-a\n+b\n")


def test_empty_and_hunkless_patches_rejected():
    with pytest.raises(PatchError):
        patch.parse("")
    with pytest.raises(PatchError, match="no hunks"):
        patch.parse("--- a/x.py\n+++ b/x.py\n")


def test_count_mismatch_rejected():
    with pytest.raises(PatchError):
        patch.parse("--- a/x.py\n+++ b/x.py\n@@ -1,3 +1,3 @@\n a\n-b\n+c\n")


def test_junk_line_rejected():
    with pytest.raises(PatchError):
        patch.parse("hello\n" + MODIFY)


def test_changed_lines_for_added():
    assert patch.changed_lines(MODIFY) == {"m.py": {3}}


def test_changed_lines_for_pure_deletion_uses_neighbours():
    assert patch.changed_lines(DELETE) == {"m.py": {2, 3}}


def test_anchors_one_per_hunk():
    assert patch.anchors(MODIFY) == [("m.py", 3)]
    assert patch.anchors(DELETE) == [("m.py", 2)]


def test_new_side_lines_cover_context_and_added():
    assert [ln for _, ln in patch.new_side_lines(MODIFY)] == [1, 2, 3, 4, 5]


def test_crlf_source_is_normalised(root):
    (root / "m.py").write_bytes(SRC.replace("\n", "\r\n").encode())
    patch.apply(str(root), MODIFY)
    assert b"\r" not in (root / "m.py").read_bytes()
