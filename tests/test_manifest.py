import hashlib
import json

import pytest

from guardbench import cli
from guardbench.defects import item_hash, manifest_hash

from test_validate import BUG, CLEAN, MOD, TEST


def _item(root, name, bug="b\n"):
    d = root / "defects" / name
    d.mkdir(parents=True)
    (d / "defect.json").write_text(json.dumps({"id": name}))
    (d / "bug.patch").write_text(bug)
    (d / "clean.patch").write_text("c\n")


def test_manifest_is_sha256_over_sorted_item_hashes(tmp_path):
    _item(tmp_path, "b-item")
    _item(tmp_path, "a-item")
    hs = sorted(item_hash(str(tmp_path / "defects" / n)) for n in ("a-item", "b-item"))
    want = hashlib.sha256("".join(h + "\n" for h in hs).encode()).hexdigest()
    assert manifest_hash(str(tmp_path)) == want


def test_manifest_changes_with_content_and_ignores_pycache(tmp_path):
    _item(tmp_path, "x")
    before = manifest_hash(str(tmp_path))
    (tmp_path / "defects" / "x" / "__pycache__").mkdir()
    (tmp_path / "defects" / "x" / "__pycache__" / "junk").write_text("zz")
    assert manifest_hash(str(tmp_path)) == before
    (tmp_path / "defects" / "x" / "bug.patch").write_text("changed\n")
    assert manifest_hash(str(tmp_path)) != before


def test_manifest_cli(tmp_path, capsys):
    _item(tmp_path, "x")
    assert cli.main(["manifest", str(tmp_path)]) == 0
    assert capsys.readouterr().out.strip() == manifest_hash(str(tmp_path))


def test_heldout_env_var_supplies_defects_and_apps_come_from_the_public_tree(tmp_path, monkeypatch, capsys):
    apps = tmp_path / "pub" / "apps" / "app"
    apps.mkdir(parents=True)
    (apps / "mod.py").write_text(MOD, newline="\n")
    (apps / "test_mod.py").write_text(TEST, newline="\n")
    held = tmp_path / "held" / "defects" / "h1"
    held.mkdir(parents=True)
    (held / "defect.json").write_text(json.dumps(
        {"id": "h1", "app": "app", "class": "fail-open", "test_module": "test_mod",
         "file": "mod.py", "start": 3, "end": 3}))
    (held / "bug.patch").write_text(BUG, newline="\n")
    (held / "clean.patch").write_text(CLEAN, newline="\n")
    monkeypatch.setenv("GUARDBENCH_HELDOUT", str(tmp_path / "held"))
    assert cli.main(["validate", "--split", "test", "--apps", str(tmp_path / "pub" / "apps"),
                     "--timeout", "30"]) == 0
    assert "ok   h1" in capsys.readouterr().out


def test_old_env_var_name_is_gone(monkeypatch):
    monkeypatch.delenv("GUARDBENCH_HELDOUT", raising=False)
    monkeypatch.setenv("GUARDBENCH_TEST_DIR", "/somewhere")
    with pytest.raises(SystemExit) as e:
        cli.main(["run", "--split", "test", "--reviewer", "random"])
    assert e.value.code == 2


def test_tree_hash_only_covers_the_named_top_level_entries(tmp_path, capsys):
    from guardbench.defects import tree_hash
    for name in ("a", "b"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "f.py").write_text(name)
    assert tree_hash(str(tmp_path), only=["a"]) != tree_hash(str(tmp_path))
    only_a = tree_hash(str(tmp_path), only=["a"])
    (tmp_path / "b" / "f.py").write_text("changed")
    assert tree_hash(str(tmp_path), only=["a"]) == only_a
    with pytest.raises(ValueError):
        tree_hash(str(tmp_path), only=["missing"])
    assert cli.main(["hash", str(tmp_path), "--only", "a"]) == 0
    assert capsys.readouterr().out.strip() == only_a
