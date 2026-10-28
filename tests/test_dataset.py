"""Gate on the shipped dev data: every pair must validate, and coverage floors must hold."""
import collections
import os
import re
import shutil

import pytest

from guardbench import cli
from guardbench import patch as P
from guardbench.baselines import random_hit_probability
from guardbench.defects import CLASSES, load_all
from guardbench.validate import run_tests, validate_defect

DEFECTS = load_all(cli.REPO_ROOT)


APPS_DIR = os.path.join(cli.REPO_ROOT, "apps")
APPS = sorted(n for n in os.listdir(APPS_DIR) if os.path.isdir(os.path.join(APPS_DIR, n)))


def test_milestone_2_floors():
    """12 apps ship; the public dev split holds 20 pairs (the rest of the 35 are held out)."""
    assert len(APPS) >= 12
    assert len(DEFECTS) >= 20
    assert len({d.app for d in DEFECTS}) >= 8


def test_dev_split_is_balanced_per_class():
    counts = collections.Counter(d.cls for d in DEFECTS)
    assert all(counts[c] >= 4 for c in CLASSES), counts
    assert max(counts.values()) - min(counts.values()) <= 1, counts


@pytest.mark.parametrize("app", APPS)
def test_every_app_passes_its_own_tests(app, tmp_path):
    work = str(tmp_path / app)
    shutil.copytree(os.path.join(APPS_DIR, app), work, ignore=shutil.ignore_patterns("__pycache__"))
    module = [n[:-3] for n in os.listdir(work) if n.startswith("test_") and n.endswith(".py")][0]
    status, out = run_tests(work, module, 60)
    assert status == "pass", out


def test_split_hash_is_a_real_hash_not_a_placeholder():
    with open(os.path.join(cli.REPO_ROOT, "prereg", "split.sha256"), encoding="utf-8") as fh:
        assert re.fullmatch(r"[0-9a-f]{64}", fh.read().strip())


def test_bug_and_clean_diffs_differ_and_touch_the_same_file():
    for d in DEFECTS:
        assert d.bug_patch != d.clean_patch
        assert ("+++ b/%s\n" % d.file) in d.bug_patch and ("+++ b/%s\n" % d.file) in d.clean_patch


@pytest.mark.parametrize("d", DEFECTS, ids=lambda d: d.id)
def test_defect_validates(d):
    assert validate_defect(d, timeout=60) == []


def test_flag_every_hunk_baseline_finds_everything_and_alarms_on_everything(capsys):
    assert cli.main(["score", "--reviewer", "hunk-all", "--json"]) == 0
    out = capsys.readouterr().out
    assert '"found": %d' % len(DEFECTS) in out


@pytest.mark.parametrize("d", DEFECTS, ids=lambda d: d.id)
def test_every_item_is_a_realistic_multi_hunk_multi_file_change(d):
    for diff in (d.bug_patch, d.clean_patch):
        files = P.parse(diff)
        hunks = sum(len(h) for _, h in files)
        assert 8 <= hunks <= 25, (d.id, hunks)
        assert 3 <= len(files) <= 6, (d.id, len(files))
    defect_hunks = [a for a in P.anchors(d.bug_patch) if a[0] == d.file and d.start - 3 <= a[1] <= d.end + 3]
    assert len(defect_hunks) == 1, "the defect must be exactly one hunk"


def test_random_baseline_stays_far_from_ceiling():
    """Kill criterion 3 guard: random must not find more than 70% of dev defects."""
    p = [random_hit_probability(d.bug_patch, d.file, d.start, d.end) for d in DEFECTS]
    assert sum(p) / len(p) < 0.15


ORIGINAL_APPS = ("authgate", "booking", "coupons", "inventory", "jobq", "pager", "ratelimit",
                 "sessions", "uploadstore", "vault", "wallet", "webhook")
ORIGINAL_APPS_HASH = "a83db71f746a6ca69313496c5119bc5099571f3503cca195069d1af1f3468704"


def test_the_original_twelve_apps_are_byte_for_byte_the_prereg_v2_apps():
    """Amendment 3: milestone 3 adds apps in new directories only; these 12 must never change."""
    from guardbench.defects import tree_hash
    assert tree_hash(APPS_DIR, only=ORIGINAL_APPS) == ORIGINAL_APPS_HASH


def test_milestone_3_floors():
    assert len(APPS) >= 20
    assert len(DEFECTS) >= 30
    assert min(collections.Counter(d.cls for d in DEFECTS).values()) >= 6
