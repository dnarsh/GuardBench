import json

import pytest

from guardbench import patch as P
from guardbench.build import BuildError, build_item, noise_applies
from guardbench.defects import Defect
from guardbench.validate import validate_defect

FUNCS = "\n\n".join(
    "def f%d(x):\n    \"\"\"Doc %d.\"\"\"\n    y = x + %d\n    z = y * 2\n    w = z - 1\n    return w - %d\n" % (i, i, i, i)
    for i in range(12))
MOD = "def is_ok(x):\n    if x < 0:\n        return False\n    return True\n\n\n" + FUNCS
OTHER = "\n\n".join("def g%d(x):\n    a = x\n    b = a\n    c = b\n    d = c\n    e = d\n    return e + %d\n" % (i, i) for i in range(8))
DOC = "\n".join("line %d" % i for i in range(30)) + "\n"
TEST = ("import unittest\nfrom mod import is_ok, f1\nfrom other import g1\n\n\nclass T(unittest.TestCase):\n"
        "    def test_neg(self):\n        self.assertFalse(is_ok(-1))\n"
        "    def test_pos(self):\n        self.assertTrue(is_ok(1))\n"
        "    def test_f(self):\n        self.assertEqual(f1(1), 2)\n        self.assertEqual(g1(1), 2)\n\n\n"
        "if __name__ == '__main__':\n    unittest.main()\n")
NOISE = ([[{"file": "mod.py", "old": "    \"\"\"Doc %d.\"\"\"\n" % i, "new": "    \"\"\"Doc %d, expanded.\"\"\"\n" % i}] for i in range(12)]
         + [[{"file": "other.py", "old": "    b = a\n    c = b\n    d = c\n    e = d\n    return e + %d\n" % i,
              "new": "    e = a\n    return e + %d\n" % i}] for i in range(8)]
         + [[{"file": "README.md", "old": "line %d\n" % i, "new": "line %d, reworded\n" % i}] for i in range(0, 30, 8)])
SPEC = {"id": "t-fail-open", "app": "app", "class": "fail-open", "file": "mod.py",
        "bug": [{"file": "mod.py", "old": "        return False\n", "new": "        return True\n"}],
        "clean": [{"file": "mod.py", "old": "    if x < 0:\n", "new": "    if not x >= 0:\n"}]}


@pytest.fixture
def app(tmp_path):
    a = tmp_path / "app"
    a.mkdir()
    for n, t in (("mod.py", MOD), ("other.py", OTHER), ("README.md", DOC), ("test_app.py", TEST)):
        (a / n).write_text(t, newline="\n")
    return str(a)


def _defect(app, item):
    d = item["defect.json"]
    return Defect(d["id"], d["app"], d["class"], d["test_module"], d["file"], d["start"], d["end"],
                  item["bug.patch"], item["clean.patch"], app)


def test_built_item_is_multi_hunk_multi_file_and_validates(app):
    item = build_item(app, SPEC, NOISE)
    bug = P.parse(item["bug.patch"])
    assert 8 <= sum(len(h) for _, h in bug) <= 25
    assert len(bug) >= 3
    assert item["defect.json"]["test_module"] == "test_app"
    assert validate_defect(_defect(app, item), timeout=30) == []


def test_location_is_the_defect_hunk_and_noise_stays_clear_of_it(app):
    item = build_item(app, SPEC, NOISE)
    d = item["defect.json"]
    assert (d["start"], d["end"]) == (3, 3)
    near = [a for a in P.anchors(item["bug.patch"]) if a[0] == "mod.py" and abs(a[1] - 3) <= 7]
    assert len(near) == 1


def test_bug_and_clean_share_the_same_noise(app):
    item = build_item(app, SPEC, NOISE)
    noise_only = lambda p: sorted(a for a in P.anchors(p) if not (a[0] == "mod.py" and a[1] <= 10))
    assert noise_only(item["bug.patch"]) == noise_only(item["clean.patch"])


def test_build_is_deterministic(app):
    assert build_item(app, SPEC, NOISE) == build_item(app, SPEC, NOISE)


def test_too_little_noise_is_an_error(app):
    with pytest.raises(BuildError):
        build_item(app, SPEC, NOISE[:2])


def test_ambiguous_or_missing_edit_text_is_an_error(app):
    bad = dict(SPEC, bug=[{"file": "mod.py", "old": "    return w", "new": "x"}])
    with pytest.raises(BuildError):
        build_item(app, bad, NOISE)
    bad = dict(SPEC, bug=[{"file": "mod.py", "old": "no such text", "new": "x"}])
    with pytest.raises(BuildError):
        build_item(app, bad, NOISE)


def test_noise_applies_cleanly_to_an_app(app):
    assert noise_applies(app, NOISE) is None
    assert "not found" in noise_applies(app, [[{"file": "mod.py", "old": "zzz", "new": "y"}]])


def test_write_items_refuses_ids_that_could_escape_the_output_dir(app, tmp_path):
    from guardbench.build import write_items
    spec = dict(SPEC, id="../evil")
    sp = tmp_path / "s.json"
    sp.write_text(json.dumps(spec))
    nd = tmp_path / "noise"
    nd.mkdir()
    (nd / "app.json").write_text(json.dumps(NOISE))
    out = tmp_path / "out"
    assert write_items([str(sp)], str(out), str(nd), str(tmp_path)) == 1
    assert not (tmp_path / "evil").exists() and not out.exists()
