import json
import os
import sys

import pytest

from guardbench import cli

from test_validate import BUG, CLEAN, MOD, TEST


@pytest.fixture
def root(tmp_path):
    app = tmp_path / "apps" / "app"
    app.mkdir(parents=True)
    (app / "mod.py").write_text(MOD, newline="\n")
    (app / "test_mod.py").write_text(TEST, newline="\n")
    d = tmp_path / "defects" / "d1"
    d.mkdir(parents=True)
    (d / "defect.json").write_text(json.dumps(
        {"id": "d1", "app": "app", "class": "fail-open", "test_module": "test_mod",
         "file": "mod.py", "start": 3, "end": 3}))
    (d / "bug.patch").write_text(BUG, newline="\n")
    (d / "clean.patch").write_text(CLEAN, newline="\n")
    return tmp_path


def test_validate_ok(root, capsys):
    assert cli.main(["validate", "--root", str(root), "--timeout", "30"]) == 0
    assert "ok   d1" in capsys.readouterr().out


def test_validate_reports_failure_and_exit_code(root, capsys):
    (root / "defects" / "d1" / "clean.patch").write_text(BUG, newline="\n")
    assert cli.main(["validate", "--root", str(root), "--timeout", "30"]) == 1
    assert "FAIL d1" in capsys.readouterr().out


def test_validate_with_no_defects_fails(tmp_path, capsys):
    assert cli.main(["validate", "--root", str(tmp_path)]) == 1


def test_score_flag_every_hunk(root, capsys):
    assert cli.main(["run", "--root", str(root), "--reviewer", "hunk-all"]) == 0
    out = capsys.readouterr().out
    assert "overall recall" in out and "1.000" in out


def test_score_json(root, capsys):
    cli.main(["run", "--root", str(root), "--reviewer", "random", "--seed", "3", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["overall"]["n"] == 1


def test_score_custom_reviewer_by_import_path(root, capsys, monkeypatch, tmp_path):
    (tmp_path / "myrev.py").write_text("def review(diff):\n    return []\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    assert cli.main(["run", "--root", str(root), "--reviewer", "myrev:review", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["overall"]["found"] == 0


def test_unknown_reviewer_is_an_error(root):
    with pytest.raises(SystemExit) as e:
        cli.main(["run", "--root", str(root), "--reviewer", "nonsense"])
    assert e.value.code == 2


def test_test_split_requires_env_var(monkeypatch):
    monkeypatch.delenv("GUARDBENCH_HELDOUT", raising=False)
    with pytest.raises(SystemExit) as e:
        cli.main(["run", "--split", "test", "--reviewer", "random"])
    assert e.value.code == 2


def test_test_split_reads_env_var(root, monkeypatch, capsys):
    monkeypatch.setenv("GUARDBENCH_HELDOUT", str(root))
    assert cli.main(["run", "--split", "test", "--reviewer", "hunk-all"]) == 0


def test_hash_prints_tree_hash(root, capsys):
    assert cli.main(["hash", str(root)]) == 0
    assert len(capsys.readouterr().out.strip()) == 64


def test_baselines_command_reports_both_baselines(root, capsys):
    assert cli.main(["baselines", "--root", str(root), "--seeds", "5"]) == 0
    out = capsys.readouterr().out
    assert "hunk-all" in out and "random expected recall" in out and "random over 5 seeds" in out


def test_custom_root_overrides_test_split_and_builtin_model_claim(root, monkeypatch, capsys):
    monkeypatch.delenv("GUARDBENCH_HELDOUT", raising=False)
    assert cli.main(["run", "--root", str(root), "--split", "test", "--reviewer", "hunk-all",
                     "--reviewer-role", "model", "--analysis-purpose", "confirmatory", "--json"]) == 0
    summary = json.loads(capsys.readouterr().out)
    analysis = summary["analysis"]
    assert analysis["split"] == "custom"
    assert analysis["purpose"] == "confirmatory"
    assert analysis["reviewer"] == {"label": "hunk-all", "role": "baseline", "transport": "builtin"}
    assert analysis["dataset"] == {"manifest": cli.manifest_hash(str(root)),
                                    "apps_hash": cli.tree_hash(str(root / "apps"))}
    # Exercise the public JSON round trip, not just the metadata constructor.
    saved = root / "run.json"
    saved.write_text(json.dumps(summary), encoding="utf-8")
    assert cli.main(["hyp", str(saved)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["analysis_status"] == "not_evaluated"
    assert "verdict" not in result["H1"]


def test_command_transport_does_not_claim_model_identity(root, capsys):
    assert cli.main(["run", "--root", str(root), "--reviewer", "command", "--json",
                     "--command", sys.executable, "-c", "print('[]')"]) == 0
    analysis = json.loads(capsys.readouterr().out)["analysis"]
    assert analysis["purpose"] == "pilot"
    assert analysis["reviewer"]["role"] == "unknown"
    assert analysis["reviewer"]["transport"] == "command"


def test_callable_reviewer_retains_explicit_role_and_effective_dev_split(root, capsys, monkeypatch, tmp_path):
    (tmp_path / "declaredrev.py").write_text("def review(diff):\n    return []\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(cli, "REPO_ROOT", str(root))
    assert cli.main(["run", "--reviewer", "declaredrev:review", "--reviewer-role", "human", "--json"]) == 0
    analysis = json.loads(capsys.readouterr().out)["analysis"]
    assert analysis["split"] == "dev"
    assert analysis["reviewer"] == {"label": "declaredrev:review", "role": "human", "transport": "callable"}


def test_known_toy_command_stays_toy_despite_declared_model(root, capsys):
    toy = os.path.join(cli.REPO_ROOT, "examples", "toy_reviewer.py")
    assert cli.main(["run", "--root", str(root), "--reviewer", "command", "--json",
                     "--reviewer-role", "model", "--command", sys.executable, toy]) == 0
    analysis = json.loads(capsys.readouterr().out)["analysis"]
    assert analysis["reviewer"]["role"] == "toy"
    assert analysis["reviewer"]["transport"] == "command"


@pytest.mark.parametrize("reviewer,role", [
    ("guardbench.baselines:flag_every_hunk", "baseline"),
    ("guardbench.reviewers:flag_every_hunk", "baseline"),
    ("examples.toy_reviewer:review", "toy"),
])
def test_shipped_callable_baselines_cannot_be_relabelled_model(root, capsys, reviewer, role):
    assert cli.main(["run", "--root", str(root), "--reviewer", reviewer,
                     "--reviewer-role", "model", "--json"]) == 0
    analysis = json.loads(capsys.readouterr().out)["analysis"]
    assert analysis["reviewer"]["role"] == role
    assert analysis["reviewer"]["transport"] == "callable"


def test_known_toy_module_command_stays_toy(root, capsys):
    assert cli.main(["run", "--root", str(root), "--reviewer", "command", "--json",
                     "--reviewer-role", "human", "--command", sys.executable,
                     "-m", "examples.toy_reviewer"]) == 0
    assert json.loads(capsys.readouterr().out)["analysis"]["reviewer"]["role"] == "toy"


def test_source_change_during_reviewer_run_emits_no_summary(root, capsys, monkeypatch):
    def reviewer(diff):
        (root / "apps" / "app" / "mod.py").write_text("changed during run\n")
        return []

    monkeypatch.setattr(cli, "_reviewer", lambda a, parser: reviewer)
    assert cli.main(["run", "--root", str(root), "--reviewer", "hunk-all", "--json"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "dataset changed" in output.err


def test_hyp_legacy_summary_is_descriptive_and_invalid_counts_are_errors(root, capsys):
    saved = root / "run.json"
    saved.write_text(json.dumps({"overall": {"found": 0, "n": 100}}), encoding="utf-8")
    assert cli.main(["hyp", str(saved)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["H1"]["recall"] == 0
    assert "verdict" not in result["H1"]
    assert result["analysis_status"] == "not_evaluated"
    saved.write_text(json.dumps({"overall": {"found": True, "n": 100}}), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        cli.main(["hyp", str(saved)])
    assert exc.value.code == 2
    assert "invalid run summary" in capsys.readouterr().err
