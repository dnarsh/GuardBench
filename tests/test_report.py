import json
import os
import shutil

import pytest

from guardbench import cli, report
from guardbench.defects import load_all

from test_cli import root  # noqa: F401  (fixture: a one-defect root)


def make(root, tmp_path, *extra):  # noqa: F811
    out = tmp_path / "RESULTS.md"
    assert cli.main(["report", "--root", str(root), "--out", str(out), "--no-toy", *extra]) == 0
    return out.read_text(encoding="utf-8")


def test_report_states_that_no_hypothesis_has_a_verdict_and_the_pilot_rule(root, tmp_path):  # noqa: F811
    text = make(root, tmp_path)
    assert "No hypothesis (H1, H2, H3) has a verdict" in text
    assert "pilot" in text and "target" in text
    assert "not evidence about any model" in text


def test_report_numbers_match_the_scorer(root, tmp_path):  # noqa: F811
    text = make(root, tmp_path)
    assert "hunk-all" in text and "1.000 [0.207, 1.000] (1/1)" in text  # Wilson interval of 1/1
    assert "fail-open" in text and "off-by-one" in text  # every class has a row, even with n = 0
    assert "Clean-twin alarm" in text


def test_report_is_deterministic(root, tmp_path):  # noqa: F811
    assert make(root, tmp_path) == make(root, tmp_path)


def test_heldout_section_and_manifest_check(root, tmp_path):  # noqa: F811
    held = tmp_path / "held"
    shutil.copytree(root / "defects", held / "defects")
    text = make(root, tmp_path, "--heldout", str(held))
    assert "Held-out" in text and "Newcombe" in text
    assert "manifest hash" in text and ("matches" in text or "MISMATCH" in text)


def test_heldout_is_skipped_without_the_private_data(root, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.delenv("GUARDBENCH_HELDOUT", raising=False)
    text = make(root, tmp_path)
    assert "Not available" in text


@pytest.mark.parametrize("count", [100, 150, 151])
def test_baseline_report_remains_descriptive_at_any_size(root, count):  # noqa: F811
    # Repeated public fixture data exercise only the report's size boundary; these
    # are not a real held-out cohort or independent benchmark observations.
    dev = load_all(root)
    heldout = [dev[0]._replace(id="synthetic-%d" % i) for i in range(count)]
    text = report.build(dev, heldout, toy=False)
    assert "No hypothesis (H1, H2, H3) has a verdict" in text
    assert "Baselines and toys remain descriptive regardless of sample size" in text
    assert "Held-out count in this run: **%d pairs**" % count in text
    if count < report.TARGET:
        assert "below the prospective reporting minimum" in text
    else:
        assert "meets the prospective size minimum only" in text
        assert "below the prospective reporting minimum" not in text
        assert "held-out split is below" not in text
    assert "Precision (point only)" in text and "F1 (point only)" in text
    assert "not hypothesis verdicts" in text


def test_toy_reviewer_row_is_labelled_a_toy(root, tmp_path):  # noqa: F811
    out = tmp_path / "R.md"
    assert cli.main(["report", "--root", str(root), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "toy" in text.lower() and "examples/toy_reviewer.py" in text


def test_committed_results_page_carries_the_no_verdict_banner():
    path = os.path.join(cli.REPO_ROOT, "docs", "RESULTS.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    assert "No hypothesis (H1, H2, H3) has a verdict" in text and "pilot" in text
    assert "Held-out manifest hash" in text and "matches" in text
