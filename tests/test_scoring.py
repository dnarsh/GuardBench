import pytest

from guardbench.baselines import flag_every_hunk, make_random
from guardbench.defects import Defect
from guardbench.scoring import run, wilson

BUG = "--- a/m.py\n+++ b/m.py\n@@ -1,5 +1,5 @@\n a\n b\n-c\n+C\n d\n e\n"
CLEAN = "--- a/m.py\n+++ b/m.py\n@@ -1,5 +1,5 @@\n a\n b\n-c\n+cc\n d\n e\n"


def defect(i, cls, start=3, end=3):
    return Defect(id=i, app="x", cls=cls, test_module="t", file="m.py", start=start,
                  end=end, bug_patch=BUG, clean_patch=CLEAN, app_dir="unused")


def test_wilson_half():
    lo, hi = wilson(5, 10)
    assert (round(lo, 4), round(hi, 4)) == (0.2366, 0.7634)


def test_wilson_zero_successes():
    lo, hi = wilson(0, 10)
    assert lo == 0.0 and round(hi, 4) == 0.2775


def test_wilson_all_successes():
    lo, hi = wilson(10, 10)
    assert round(lo, 4) == 0.7225 and hi == 1.0


def test_wilson_80_of_100():
    lo, hi = wilson(80, 100)
    assert (round(lo, 4), round(hi, 4)) == (0.7112, 0.8666)


def test_wilson_empty_sample_is_uninformative():
    assert wilson(0, 0) == (0.0, 1.0)


@pytest.mark.parametrize("k,n", [(-1, 5), (6, 5)])
def test_wilson_rejects_impossible_counts(k, n):
    with pytest.raises(ValueError):
        wilson(k, n)


def test_perfect_reviewer_with_no_false_alarms():
    ds = [defect("a", "fail-open"), defect("b", "off-by-one")]

    def rev(diff):
        return [{"file": "m.py", "line": 3, "text": "bug"}] if "+C" in diff else []

    s = run(ds, rev)
    assert s["overall"]["recall"] == 1.0
    assert s["clean_alarm"]["rate"] == 0.0
    assert s["precision"] == 1.0 and s["f1"] == 1.0
    assert s["per_class"]["fail-open"]["n"] == 1


def test_silent_reviewer_has_undefined_precision_and_zero_f1():
    s = run([defect("a", "fail-open")], lambda d: [])
    assert s["overall"]["recall"] == 0.0
    assert s["precision"] is None and s["f1"] == 0.0


def test_flag_everything_reviewer_alarms_on_every_clean_twin():
    s = run([defect("a", "fail-open"), defect("b", "off-by-one")], flag_every_hunk)
    assert s["overall"]["recall"] == 1.0
    assert s["clean_alarm"]["rate"] == 1.0
    assert s["precision"] == 0.5  # 1 hit comment of 2 on the bug diff + 2 on clean twins -> 2/4


def test_comment_far_from_defect_is_miss():
    s = run([defect("a", "fail-open", start=40, end=41)], flag_every_hunk)
    assert s["overall"]["found"] == 0


def test_multiple_hits_on_one_defect_count_once_for_recall():
    rev = lambda d: [{"file": "m.py", "line": 3}, {"file": "m.py", "line": 4}]
    s = run([defect("a", "fail-open")], rev)
    assert s["overall"]["found"] == 1 and s["tp_comments"] == 2


def test_groups_split_guard_and_logic():
    ds = [defect("a", "fail-open"), defect("b", "race-condition")]
    rev = lambda d: [{"file": "m.py", "line": 3}] if "+C" in d else []
    s = run(ds, rev)
    assert s["per_group"]["guard"]["n"] == 1 and s["per_group"]["logic"]["n"] == 1


def test_non_list_reviewer_output_raises():
    with pytest.raises(ValueError):
        run([defect("a", "fail-open")], lambda d: None)


def test_malformed_comments_count_as_comments_never_hits():
    s = run([defect("a", "fail-open")], lambda d: ["junk"])
    assert s["overall"]["found"] == 0 and s["precision"] == 0.0


def test_no_defects_raises():
    with pytest.raises(ValueError):
        run([], lambda d: [])


def test_flag_every_hunk_one_comment_per_hunk():
    assert flag_every_hunk(BUG) == [{"file": "m.py", "line": 3, "text": "flagged hunk"}]


def test_random_is_deterministic_and_within_diff():
    r = make_random(seed=7)
    assert r(BUG) == r(BUG)
    assert r(BUG)[0]["line"] in range(1, 6) and r(BUG)[0]["file"] == "m.py"


def test_random_differs_across_seeds_eventually():
    lines = {make_random(seed=s)(BUG)[0]["line"] for s in range(30)}
    assert len(lines) > 1


def test_baselines_on_unparseable_diff_return_nothing():
    assert make_random()("not a diff") == []
