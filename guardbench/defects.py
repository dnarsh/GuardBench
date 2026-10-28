"""Defect loader and tree hash.

Layout of a root directory (the repo itself for dev, $GUARDBENCH_TEST_DIR for test):
    apps/<app>/...                  clean app files plus its unittest module
    defects/<id>/defect.json        metadata (see FIELDS)
    defects/<id>/bug.patch          diff that plants the flaw
    defects/<id>/clean.patch        same-shaped diff without the flaw
"""
import hashlib
import json
import os
import re
from collections import namedtuple

GROUPS = {
    "fail-open": "guard",
    "removed-validation": "guard",
    "secret-leakage": "guard",
    "race-condition": "logic",
    "off-by-one": "logic",
}
CLASSES = tuple(GROUPS)
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

Defect = namedtuple("Defect", "id app cls test_module file start end bug_patch clean_patch app_dir")


def _bad_path(p):
    return (not p or "\\" in p or ":" in p or p.startswith("/")
            or any(s in ("", ".", "..") for s in p.split("/")))


def load_one(defect_dir, apps_dir):
    with open(os.path.join(defect_dir, "defect.json"), encoding="utf-8") as fh:
        m = json.load(fh)
    for k in ("id", "app", "class", "test_module", "file", "start", "end"):
        if k not in m:
            raise ValueError("%s: missing field %r" % (defect_dir, k))
    if not NAME_RE.match(str(m["id"])) or not NAME_RE.match(str(m["app"])):
        raise ValueError("%s: bad id or app name" % defect_dir)
    if m["id"] != os.path.basename(os.path.normpath(defect_dir)):
        raise ValueError("%s: directory name must match id" % defect_dir)
    if m["class"] not in CLASSES:
        raise ValueError("%s: unknown class %r" % (m["id"], m["class"]))
    if not MODULE_RE.match(str(m["test_module"])):
        raise ValueError("%s: bad test_module" % m["id"])
    if not isinstance(m["file"], str) or _bad_path(m["file"]):
        raise ValueError("%s: bad file path" % m["id"])
    s, e = m["start"], m["end"]
    if any(type(x) is not int for x in (s, e)) or not 1 <= s <= e:
        raise ValueError("%s: need integers 1 <= start <= end" % m["id"])
    with open(os.path.join(defect_dir, "bug.patch"), encoding="utf-8", newline="") as fh:
        bug = fh.read()
    with open(os.path.join(defect_dir, "clean.patch"), encoding="utf-8", newline="") as fh:
        clean = fh.read()
    return Defect(m["id"], m["app"], m["class"], m["test_module"], m["file"], s, e,
                  bug, clean, os.path.join(apps_dir, m["app"]))


def load_all(root, apps_dir=None):
    """Load every defect under root/defects; apps come from apps_dir (default root/apps)."""
    ddir = os.path.join(root, "defects")
    if not os.path.isdir(ddir):
        return []
    return [load_one(os.path.join(ddir, n), apps_dir or os.path.join(root, "apps"))
            for n in sorted(os.listdir(ddir)) if os.path.isdir(os.path.join(ddir, n))]


def tree_hash(directory):
    """sha256 over sorted '<posix relpath>\\0<sha256 of bytes>\\n' lines."""
    lines = []
    for base, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            full = os.path.join(base, f)
            rel = os.path.relpath(full, directory).replace(os.sep, "/")
            with open(full, "rb") as fh:
                lines.append("%s\0%s\n" % (rel, hashlib.sha256(fh.read()).hexdigest()))
    return hashlib.sha256("".join(sorted(lines)).encode("utf-8")).hexdigest()


def item_hash(item_dir):
    """Hash of one defect item (its defect.json, bug.patch and clean.patch bytes)."""
    return tree_hash(item_dir)


def manifest_hash(root):
    """sha256 over the sorted item hashes of root/defects/*; this is prereg/split.sha256."""
    ddir = os.path.join(root, "defects")
    hs = sorted(item_hash(os.path.join(ddir, n)) for n in os.listdir(ddir)
                if os.path.isdir(os.path.join(ddir, n)))
    return hashlib.sha256("".join(h + "\n" for h in hs).encode("utf-8")).hexdigest()
