import json
import sys

import pytest

from guardbench import cli, reviewers

from test_cli import root  # noqa: F401  (fixture: a one-defect root)
from test_validate import BUG

FINDING = "import sys, json\nsys.stdin.read()\nprint(json.dumps(%s))\n"


def script(tmp_path, body):
    p = tmp_path / "rev.py"
    p.write_text(body, newline="\n")
    return str(p)


def test_command_reviewer_reads_diff_on_stdin_and_parses_findings(tmp_path):
    p = script(tmp_path, "import sys, json\nd = sys.stdin.read()\n"
                         "print(json.dumps([{'file': 'mod.py', 'line': 3, 'text': str(len(d) > 0)}]))\n")
    r = reviewers.command_reviewer([sys.executable, p], timeout=30)
    assert r(BUG) == [{"file": "mod.py", "line": 3, "text": "True"}]


def test_findings_object_form_is_accepted(tmp_path):
    p = script(tmp_path, FINDING % "{'findings': [{'file': 'a.py', 'line': 1}]}")
    assert reviewers.command_reviewer([sys.executable, p], 30)("d") == [{"file": "a.py", "line": 1, "text": ""}]


@pytest.mark.parametrize("out", [
    "'not a list'", "[1]", "[{'file': 'a.py'}]", "[{'file': 'a.py', 'line': 'x'}]",
    "[{'file': 'a.py', 'line': 0}]", "[{'file': 3, 'line': 1}]", "[{'file': 'a.py', 'line': True}]",
])
def test_bad_schema_is_a_reviewer_error(tmp_path, out):
    p = script(tmp_path, FINDING % out)
    with pytest.raises(reviewers.ReviewerError):
        reviewers.command_reviewer([sys.executable, p], 30)("d")


def test_non_json_nonzero_exit_and_timeout_are_errors(tmp_path):
    for body, t in (("print('hello')\n", 30), ("import sys\nsys.exit(3)\n", 30),
                    ("import time\ntime.sleep(60)\n", 1)):
        with pytest.raises(reviewers.ReviewerError):
            reviewers.command_reviewer([sys.executable, script(tmp_path, body)], t)("d")


def test_missing_program_is_a_reviewer_error():
    with pytest.raises(reviewers.ReviewerError):
        reviewers.command_reviewer(["definitely-not-a-program-xyz"], 5)("d")


def test_builtin_names():
    assert reviewers.get("hunk-all")(BUG)[0]["file"] == "mod.py"
    assert reviewers.get("flag-every-hunk") is reviewers.get("hunk-all")
    assert reviewers.get("random", seed=1)(BUG) == reviewers.get("random", seed=1)(BUG)
    with pytest.raises(reviewers.ReviewerError):
        reviewers.get("command")  # needs a command
    with pytest.raises(reviewers.ReviewerError):
        reviewers.get("nonsense")


def test_run_command_end_to_end(root, tmp_path, capsys):  # noqa: F811
    p = script(tmp_path, FINDING % "[{'file': 'mod.py', 'line': 3, 'text': 'x'}]")
    assert cli.main(["run", "--root", str(root), "--reviewer", "command", "--json",
                     "--command", sys.executable, p]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["overall"]["found"] == 1 and data["clean_alarm"]["alarms"] == 1


def test_run_with_failing_command_exits_nonzero(root, tmp_path, capsys):  # noqa: F811
    p = script(tmp_path, "import sys\nsys.exit(2)\n")
    assert cli.main(["run", "--root", str(root), "--reviewer", "command", "--command", sys.executable, p]) == 1
    assert "reviewer error" in capsys.readouterr().err


def test_run_hunk_all_and_random_builtin(root, capsys):  # noqa: F811
    for name in ("hunk-all", "random"):
        assert cli.main(["run", "--root", str(root), "--reviewer", name, "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["overall"]["n"] == 1


def test_output_cap_is_enforced_while_streaming_not_after_buffering(tmp_path):
    """A reviewer that never stops printing must be cut off at the cap, long before its timeout."""
    import time
    p = script(tmp_path, "import sys\nwhile True:\n    sys.stdout.write('x' * 65536)\n    sys.stdout.flush()\n")
    t0 = time.time()
    with pytest.raises(reviewers.ReviewerError, match="printed more than"):
        reviewers.command_reviewer([sys.executable, p], timeout=20)("d")
    assert time.time() - t0 < 10


def test_stderr_flood_is_bounded_and_the_tail_is_reported(tmp_path):
    p = script(tmp_path, "import sys\nsys.stderr.write('e' * 3000000 + 'THE-END')\nsys.exit(4)\n")
    with pytest.raises(reviewers.ReviewerError) as e:
        reviewers.command_reviewer([sys.executable, p], timeout=20)("d")
    assert "THE-END" in str(e.value) and len(str(e.value)) < 1000


def test_large_diff_on_stdin_with_a_reviewer_that_reads_late(tmp_path):
    p = script(tmp_path, "import sys, json\nd = sys.stdin.read()\nprint(json.dumps([{'file': 'a.py', 'line': len(d) % 7 + 1}]))\n")
    big = "x" * 5000000
    assert reviewers.command_reviewer([sys.executable, p], 30)(big)[0]["file"] == "a.py"
