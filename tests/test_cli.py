import json

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
