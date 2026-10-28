import pytest

from guardbench.matcher import is_hit


def c(file="a.py", line=10):
    return {"file": file, "line": line, "text": "x"}


def test_inside_range():
    assert is_hit(c(line=12), "a.py", 10, 14)


def test_exact_start_and_end():
    assert is_hit(c(line=10), "a.py", 10, 14)
    assert is_hit(c(line=14), "a.py", 10, 14)


def test_three_lines_before_start_is_hit():
    assert is_hit(c(line=7), "a.py", 10, 14)


def test_four_lines_before_start_is_miss():
    assert not is_hit(c(line=6), "a.py", 10, 14)


def test_three_lines_after_end_is_hit():
    assert is_hit(c(line=17), "a.py", 10, 14)


def test_four_lines_after_end_is_miss():
    assert not is_hit(c(line=18), "a.py", 10, 14)


def test_single_line_range():
    assert is_hit(c(line=13), "a.py", 10, 10)
    assert not is_hit(c(line=14), "a.py", 10, 10)


def test_range_near_file_start_does_not_go_negative():
    assert is_hit(c(line=1), "a.py", 2, 2)


def test_wrong_file_is_miss():
    assert not is_hit(c(file="b.py", line=10), "a.py", 10, 14)


def test_same_basename_other_dir_is_miss():
    assert not is_hit(c(file="x/a.py", line=10), "a.py", 10, 14)


def test_path_normalisation():
    assert is_hit(c(file="./a.py"), "a.py", 10, 14)
    assert is_hit(c(file="pkg\\a.py"), "pkg/a.py", 10, 14)


def test_custom_tolerance():
    assert not is_hit(c(line=9), "a.py", 10, 14, tol=0)
    assert is_hit(c(line=19), "a.py", 10, 14, tol=5)


@pytest.mark.parametrize("line", [True, "10", 10.0, None, -1, 0])
def test_non_integer_or_nonpositive_line_is_miss(line):
    assert not is_hit(c(line=line), "a.py", 1, 14)


@pytest.mark.parametrize("comment", [{}, {"file": "a.py"}, {"line": 10}, None, "x", [1]])
def test_malformed_comment_is_miss(comment):
    assert not is_hit(comment, "a.py", 10, 14)


def test_non_string_file_is_miss():
    assert not is_hit({"file": 5, "line": 10}, "a.py", 10, 14)
