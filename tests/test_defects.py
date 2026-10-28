import json

import pytest

from guardbench.defects import CLASSES, GROUPS, load_all, load_one, tree_hash


def make(root, id="d1", app="app", **over):
    meta = {"id": id, "app": app, "class": "fail-open", "test_module": "test_x",
            "file": "m.py", "start": 2, "end": 3}
    meta.update(over)
    d = root / "defects" / id
    d.mkdir(parents=True, exist_ok=True)
    (d / "defect.json").write_text(json.dumps(meta))
    (d / "bug.patch").write_text("bug")
    (d / "clean.patch").write_text("clean")
    (root / "apps" / app).mkdir(parents=True, exist_ok=True)
    return d


def test_load_one(tmp_path):
    d = load_one(str(make(tmp_path)), str(tmp_path / "apps"))
    assert (d.id, d.app, d.cls, d.file, d.start, d.end) == ("d1", "app", "fail-open", "m.py", 2, 3)
    assert d.bug_patch == "bug" and d.clean_patch == "clean"
    assert d.app_dir == str(tmp_path / "apps" / "app")


def test_load_all_sorted_and_empty(tmp_path):
    assert load_all(str(tmp_path)) == []
    make(tmp_path, "b")
    make(tmp_path, "a")
    assert [d.id for d in load_all(str(tmp_path))] == ["a", "b"]


@pytest.mark.parametrize("over", [
    {"class": "nonsense"}, {"id": "Bad Id"}, {"id": "../x"}, {"app": "../x"},
    {"start": 5, "end": 2}, {"start": 0}, {"start": "2"}, {"test_module": "a.b"},
    {"file": "../m.py"}, {"file": "/abs.py"}, {"file": "a\\b.py"},
])
def test_invalid_metadata_rejected(tmp_path, over):
    over = dict(over)
    d = make(tmp_path, over.pop("id", "d1"), **over)
    with pytest.raises(ValueError):
        load_one(str(d), str(tmp_path / "apps"))


def test_missing_field_rejected(tmp_path):
    d = make(tmp_path)
    meta = json.loads((d / "defect.json").read_text())
    del meta["file"]
    (d / "defect.json").write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="file"):
        load_one(str(d), str(tmp_path / "apps"))


def test_directory_name_must_match_id(tmp_path):
    d = make(tmp_path, "d1")
    meta = json.loads((d / "defect.json").read_text())
    meta["id"] = "other"
    (d / "defect.json").write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="match"):
        load_one(str(d), str(tmp_path / "apps"))


def test_every_class_has_a_group():
    assert set(GROUPS) == set(CLASSES)
    assert set(GROUPS.values()) == {"guard", "logic"}


def test_tree_hash_changes_with_content_and_is_stable(tmp_path):
    (tmp_path / "a.txt").write_text("1")
    h1 = tree_hash(str(tmp_path))
    assert h1 == tree_hash(str(tmp_path)) and len(h1) == 64
    (tmp_path / "a.txt").write_text("2")
    assert tree_hash(str(tmp_path)) != h1


def test_tree_hash_depends_on_file_names(tmp_path):
    (tmp_path / "a.txt").write_text("1")
    h1 = tree_hash(str(tmp_path))
    (tmp_path / "a.txt").rename(tmp_path / "b.txt")
    assert tree_hash(str(tmp_path)) != h1
