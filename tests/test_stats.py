import pytest

from guardbench.scoring import h1_verdict, hypotheses, newcombe_diff, wilson


def test_newcombe_matches_the_published_worked_example():
    # Newcombe (1998), Statistics in Medicine 17:873, table II row 1: 56/70 vs 48/80,
    # method 10 (hybrid score): difference 0.2000, interval 0.0524 to 0.3339.
    d, lo, hi = newcombe_diff(56, 70, 48, 80)
    assert round(d, 4) == 0.2
    assert round(lo, 4) == 0.0524
    assert round(hi, 4) == 0.3339


def test_newcombe_matches_a_hand_computed_value():
    # 15/20 vs 5/20: Wilson(15/20) = [0.5313, 0.8881]; Wilson(5/20) = [0.1119, 0.4687]
    # d = 0.5; L = 0.5 - sqrt((0.75-0.5313)^2 + (0.4687-0.25)^2) = 0.5 - 0.3093 = 0.1907
    # U = 0.5 + sqrt((0.8881-0.75)^2 + (0.25-0.1119)^2) = 0.5 + 0.1953 = 0.6953
    d, lo, hi = newcombe_diff(15, 20, 5, 20)
    assert d == pytest.approx(0.5)
    assert lo == pytest.approx(0.1907, abs=5e-4)
    assert hi == pytest.approx(0.6953, abs=5e-4)


def test_newcombe_is_antisymmetric_and_centred_for_equal_groups():
    d, lo, hi = newcombe_diff(9, 30, 9, 30)
    assert d == 0 and lo == pytest.approx(-hi)
    a, b = newcombe_diff(20, 60, 10, 40), newcombe_diff(10, 40, 20, 60)
    assert a[0] == pytest.approx(-b[0]) and a[1] == pytest.approx(-b[2]) and a[2] == pytest.approx(-b[1])


def test_newcombe_stays_inside_minus_one_and_one_at_the_extremes():
    d, lo, hi = newcombe_diff(30, 30, 0, 30)
    assert d == 1 and -1 <= lo < 1 and hi == pytest.approx(1)


def test_newcombe_rejects_empty_groups():
    with pytest.raises(ValueError):
        newcombe_diff(0, 0, 1, 2)


def test_h1_verdict_follows_the_preregistered_rule():
    # upper bound < 0.75 supports; lower bound >= 0.75 refutes; otherwise inconclusive
    assert h1_verdict(30, 100) == "supported"
    assert h1_verdict(95, 100) == "refuted"
    assert h1_verdict(7, 10) == "inconclusive"
    assert wilson(60, 100)[1] < 0.75 and h1_verdict(60, 100) == "supported"
    assert h1_verdict(0, 0) == "inconclusive"


def _hypothesis_summary():
    def rate(found, n):
        return {"found": found, "n": n, "recall": found / n, "ci": wilson(found, n)}

    return {
        "overall": rate(0, 100),
        "per_group": {"guard": rate(0, 60), "logic": rate(0, 40)},
    }


def _analysis_metadata(**changes):
    metadata = {
        "schema_version": 1,
        "purpose": "confirmatory",
        "split": "heldout",
        "protocol": "prereg-v3",
        "dataset": {"manifest": "a" * 64, "apps_hash": "b" * 64},
        "reviewer": {"label": "synthetic model", "role": "model", "transport": "command"},
    }
    metadata.update(changes)
    return metadata


def _assert_descriptive_hypotheses(result):
    # These counts would support H1 without an eligibility check. Check the public
    # result directly so regressions fail on a scientific claim, not a missing key.
    assert "verdict" not in result.get("H1", {}), result
    assert "verdict" not in result.get("H3", {}), result
    assert result.get("analysis_status") == "not_evaluated", result
    assert isinstance(result.get("analysis_reasons"), list), result
    assert result.get("analysis_reasons"), result
    assert result.get("H1", {}).get("recall") == 0.0
    assert result.get("H1", {}).get("ci") == pytest.approx(wilson(0, 100))
    assert result.get("H3", {}).get("diff") == 0.0
    assert result.get("H3", {}).get("ci") == pytest.approx(newcombe_diff(0, 60, 0, 40)[1:])


def test_hypotheses_missing_analysis_metadata_are_descriptive_only():
    _assert_descriptive_hypotheses(hypotheses(_hypothesis_summary()))


@pytest.mark.parametrize("metadata", [None, {}, {
    "purpose": "confirmatory", "split": "heldout", "reviewer": "synthetic model",
}], ids=["null", "empty", "unversioned"])
def test_hypotheses_legacy_analysis_metadata_are_descriptive_only(metadata):
    summary = _hypothesis_summary()
    summary["analysis"] = metadata
    _assert_descriptive_hypotheses(hypotheses(summary))


@pytest.mark.parametrize("split", ["dev", "custom"])
def test_hypotheses_dev_or_custom_split_are_descriptive_only(split):
    summary = _hypothesis_summary()
    summary["analysis"] = _analysis_metadata(split=split)
    _assert_descriptive_hypotheses(hypotheses(summary))


def test_hypotheses_pilot_purpose_is_descriptive_only():
    summary = _hypothesis_summary()
    summary["analysis"] = _analysis_metadata(purpose="pilot")
    _assert_descriptive_hypotheses(hypotheses(summary))


@pytest.mark.parametrize("role", ["baseline", "toy", "unknown"])
def test_hypotheses_baseline_toy_or_unknown_role_are_descriptive_only(role):
    summary = _hypothesis_summary()
    summary["analysis"] = _analysis_metadata(
        reviewer={"label": "synthetic model", "role": role, "transport": "command"})
    _assert_descriptive_hypotheses(hypotheses(summary))


def test_hypotheses_current_v3_cohort_cannot_be_promoted_by_supplied_flags():
    summary = _hypothesis_summary()
    summary["analysis"] = _analysis_metadata(dataset={
        "manifest": "ae29a20ee5b1f9e2a86d714805f5e20776148f268ef9e45375ef70b7c5927990",
        "apps_hash": "8b3fd772266b3ec05f073db8a3632d10ae99507c2879b304d7fb7a3b4f97cc1d",
    }, eligible=True, mode="confirmatory", minimum=100)
    _assert_descriptive_hypotheses(hypotheses(summary))


@pytest.fixture
def confirmatory_metadata(monkeypatch):
    from guardbench.analysis import PROTOCOLS

    monkeypatch.setitem(PROTOCOLS, "synthetic-future", {
        "manifest": "a" * 64, "apps_hash": "b" * 64,
        "n": 150, "mode": "confirmatory", "minimum": 150,
    })
    return _analysis_metadata(protocol="synthetic-future")


def _confirmatory_summary(metadata, guard_found=45, logic_found=0):
    # Deliberately forged derived fields: counts must be the source of estimates.
    def rate(found, n):
        return {"found": found, "n": n, "recall": -99, "ci": [99, 100]}

    return {
        "analysis": metadata,
        "overall": rate(guard_found + logic_found, 150),
        "per_group": {"guard": rate(guard_found, 90), "logic": rate(logic_found, 60)},
    }


def _assert_ineligible(result, reason):
    assert result.get("eligible") is False, result
    assert isinstance(result.get("reasons"), list), result
    assert any(reason in explanation for explanation in result.get("reasons", [])), result


def _assert_without_verdicts(result):
    assert result.get("analysis_status") == "not_evaluated", result
    assert isinstance(result.get("analysis_reasons"), list), result
    assert result.get("analysis_reasons"), result
    assert "verdict" not in result.get("H1", {}), result
    assert "verdict" not in result.get("H3", {}), result
    assert result.get("H1", {}).get("recall") == pytest.approx(45 / 150)
    assert result.get("H1", {}).get("ci") == pytest.approx(wilson(45, 150))
    assert result.get("H3", {}).get("diff") == pytest.approx(0.5)
    assert result.get("H3", {}).get("ci") == pytest.approx(newcombe_diff(45, 90, 0, 60)[1:])


@pytest.mark.parametrize("role", ["model", "human"])
@pytest.mark.parametrize("transport", ["command", "callable"])
def test_eligibility_accepts_registered_confirmatory_reviewer(
        confirmatory_metadata, role, transport):
    from guardbench.analysis import assess_eligibility

    confirmatory_metadata["reviewer"].update(role=role, transport=transport)
    result = assess_eligibility(confirmatory_metadata, 150)
    assert result.get("eligible") is True, result
    assert result.get("reasons") == [], result


@pytest.mark.parametrize("path,value,reason", [
    (("schema_version",), 2, "schema_version"),
    (("schema_version",), True, "schema_version"),
    (("schema_version",), 1.0, "schema_version"),
    (("purpose",), "pilot", "purpose"),
    (("split",), "dev", "split"),
    (("split",), "custom", "split"),
    (("protocol",), "unregistered", "not registered"),
    (("dataset", "manifest"), "c" * 64, "manifest"),
    (("dataset", "apps_hash"), "c" * 64, "apps_hash"),
    (("reviewer", "role"), "baseline", "role"),
    (("reviewer", "role"), "toy", "role"),
    (("reviewer", "role"), "unknown", "role"),
    (("reviewer", "transport"), "builtin", "transport"),
    (("reviewer", "transport"), "unknown", "transport"),
    (("reviewer", "label"), None, "label"),
    (("reviewer", "label"), "", "label"),
    (("reviewer", "label"), "   ", "label"),
])
def test_eligibility_rejects_each_invalid_metadata_field(
        confirmatory_metadata, path, value, reason):
    from guardbench.analysis import assess_eligibility

    destination = confirmatory_metadata
    for key in path[:-1]:
        destination = destination[key]
    destination[path[-1]] = value
    _assert_ineligible(assess_eligibility(confirmatory_metadata, 150), reason)
    _assert_without_verdicts(hypotheses(_confirmatory_summary(confirmatory_metadata)))


@pytest.mark.parametrize("metadata", [None, False, [], "legacy"])
def test_eligibility_malformed_metadata_fails_closed(metadata):
    from guardbench.analysis import assess_eligibility

    _assert_ineligible(assess_eligibility(metadata, 150), "metadata")
    _assert_without_verdicts(hypotheses(_confirmatory_summary(metadata)))


def test_eligibility_rejects_missing_reviewer_label(confirmatory_metadata):
    from guardbench.analysis import assess_eligibility

    del confirmatory_metadata["reviewer"]["label"]
    _assert_ineligible(assess_eligibility(confirmatory_metadata, 150), "label")
    _assert_without_verdicts(hypotheses(_confirmatory_summary(confirmatory_metadata)))


def test_eligibility_rejects_wrong_cohort_count_above_target(confirmatory_metadata):
    from guardbench.analysis import assess_eligibility

    _assert_ineligible(assess_eligibility(confirmatory_metadata, 151), "defect count")


def test_eligibility_target_cannot_be_lowered_by_registry_or_caller(
        confirmatory_metadata, monkeypatch):
    from guardbench.analysis import PROTOCOLS, TARGET, assess_eligibility

    assert TARGET == 150
    record = dict(PROTOCOLS["synthetic-future"], n=149, minimum=149)
    monkeypatch.setitem(PROTOCOLS, "synthetic-future", record)
    confirmatory_metadata.update(eligible=True, minimum=1)
    _assert_ineligible(assess_eligibility(confirmatory_metadata, 149), "minimum")


def test_eligibility_caller_minimum_cannot_lower_registered_minimum(
        confirmatory_metadata, monkeypatch):
    from guardbench.analysis import PROTOCOLS, assess_eligibility

    record = dict(PROTOCOLS["synthetic-future"], minimum=151)
    monkeypatch.setitem(PROTOCOLS, "synthetic-future", record)
    confirmatory_metadata.update(eligible=True, minimum=1)
    _assert_ineligible(assess_eligibility(confirmatory_metadata, 150), "minimum")


def test_eligibility_current_v3_registry_is_pilot_even_with_caller_flags():
    from guardbench.analysis import assess_eligibility

    metadata = _analysis_metadata(dataset={
        "manifest": "ae29a20ee5b1f9e2a86d714805f5e20776148f268ef9e45375ef70b7c5927990",
        "apps_hash": "8b3fd772266b3ec05f073db8a3632d10ae99507c2879b304d7fb7a3b4f97cc1d",
    }, eligible=True, mode="confirmatory", minimum=1)
    _assert_ineligible(assess_eligibility(metadata, 100), "pilot")


@pytest.mark.parametrize("guard_found,logic_found,h1,h3", [
    (45, 0, "supported", "supported"),
    (86, 58, "refuted", "inconclusive"),
    (67, 45, "inconclusive", "inconclusive"),
    (0, 60, "supported", "supported"),
    (45, 30, "supported", "inconclusive"),
], ids=["h1-supported-h3-positive", "h1-refuted", "h1-inconclusive",
        "h3-negative", "h3-zero"])
def test_eligible_hypotheses_recompute_estimates_and_apply_verdict_rules(
        confirmatory_metadata, guard_found, logic_found, h1, h3):
    result = hypotheses(_confirmatory_summary(confirmatory_metadata, guard_found, logic_found))
    found = guard_found + logic_found
    difference, lo, hi = newcombe_diff(guard_found, 90, logic_found, 60)
    assert result.get("analysis_status") == "evaluated", result
    assert result.get("analysis_reasons") == [], result
    assert result.get("H1", {}).get("recall") == pytest.approx(found / 150)
    assert result.get("H1", {}).get("ci") == pytest.approx(wilson(found, 150))
    assert result.get("H1", {}).get("verdict") == h1
    assert result.get("H3", {}).get("diff") == pytest.approx(difference)
    assert result.get("H3", {}).get("ci") == pytest.approx([lo, hi])
    assert result.get("H3", {}).get("verdict") == h3


def test_eligible_hypotheses_can_evaluate_h1_without_group_data(confirmatory_metadata):
    summary = _confirmatory_summary(confirmatory_metadata)
    del summary["per_group"]
    result = hypotheses(summary)
    assert result.get("analysis_status") == "evaluated", result
    assert result.get("H1", {}).get("verdict") == "supported"
    assert "H3" not in result


@pytest.mark.parametrize("scope", ["overall", "guard", "logic"])
@pytest.mark.parametrize("field,value", [
    ("found", True), ("found", 1.0), ("found", -1), ("found", 151),
    ("n", True), ("n", 150.0), ("n", -1),
])
def test_hypotheses_reject_malformed_integer_counts(
        confirmatory_metadata, scope, field, value):
    summary = _confirmatory_summary(confirmatory_metadata)
    rate = summary["overall"] if scope == "overall" else summary["per_group"][scope]
    rate[field] = value
    with pytest.raises(ValueError):
        hypotheses(summary)


@pytest.mark.parametrize("scope,field,value", [
    ("overall", "n", 151),
    ("overall", "found", 46),
    ("guard", "n", 89),
    ("guard", "found", 44),
])
def test_hypotheses_reject_group_totals_inconsistent_with_overall(
        confirmatory_metadata, scope, field, value):
    summary = _confirmatory_summary(confirmatory_metadata)
    rate = summary["overall"] if scope == "overall" else summary["per_group"][scope]
    rate[field] = value
    with pytest.raises(ValueError):
        hypotheses(summary)


def test_hypotheses_reject_an_incomplete_group_partition(confirmatory_metadata):
    summary = _confirmatory_summary(confirmatory_metadata)
    del summary["per_group"]["logic"]
    with pytest.raises(ValueError):
        hypotheses(summary)


@pytest.mark.parametrize("guard_index", [0, 1], ids=["H1", "H3"])
def test_guard_removal_reaches_the_descriptive_verdict_oracle(
        confirmatory_metadata, tmp_path, guard_index):
    """Remove each verdict guard from a copy of the actual module, not a mock."""
    import importlib.util
    from pathlib import Path

    from guardbench import scoring

    original = Path(scoring.__file__).read_bytes()
    source = original.decode("utf-8")
    guard = 'if eligibility["eligible"]:'
    parts = source.split(guard)
    assert len(parts) == 3  # Both scientific verdict publication boundaries exist.
    mutant = guard.join(parts[:guard_index + 1]) + "if True:" + guard.join(parts[guard_index + 1:])
    path = tmp_path / "scoring_mutant.py"
    path.write_text(mutant, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("guardbench._eligibility_mutant", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Syntax/import failure is not mutation proof.
    control = module.hypotheses(_confirmatory_summary(confirmatory_metadata))
    assert control["analysis_status"] == "evaluated"
    assert control["H1"]["verdict"] == "supported"
    assert control["H3"]["verdict"] == "supported"
    with pytest.raises(AssertionError, match="verdict"):
        _assert_descriptive_hypotheses(module.hypotheses(_hypothesis_summary()))
    # The unchanged real implementation still satisfies the same negative oracle.
    _assert_descriptive_hypotheses(hypotheses(_hypothesis_summary()))
    assert Path(scoring.__file__).read_bytes() == original
