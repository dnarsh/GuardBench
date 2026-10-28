"""Gate on the shipped dev data: every pair must validate, and coverage floors must hold."""
import collections

import pytest

from guardbench import cli
from guardbench import patch as P
from guardbench.baselines import random_hit_probability
from guardbench.defects import CLASSES, load_all
from guardbench.validate import validate_defect

DEFECTS = load_all(cli.REPO_ROOT)


def test_foundation_floor_apps_and_pairs():
    assert len({d.app for d in DEFECTS}) >= 5
    assert len(DEFECTS) >= 10


def test_every_class_has_at_least_two_defects():
    counts = collections.Counter(d.cls for d in DEFECTS)
    assert all(counts[c] >= 2 for c in CLASSES), counts


def test_every_app_has_at_least_two_defects():
    counts = collections.Counter(d.app for d in DEFECTS)
    assert min(counts.values()) >= 2, counts


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
