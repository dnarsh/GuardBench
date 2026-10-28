"""Gate on the shipped dev data: every pair must validate, and coverage floors must hold."""
import collections

import pytest

from guardbench import cli
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
