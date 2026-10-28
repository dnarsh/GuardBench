import json
import os
import subprocess
import sys

import pytest

from guardbench import cli, reviewers

EXAMPLE = os.path.join(cli.REPO_ROOT, "examples", "toy_reviewer.py")

REMOVED_CHECK = """--- a/m.py
+++ b/m.py
@@ -10,6 +10,4 @@ def check(x):
     a = 1
-    if x > 3:
-        raise ValueError("too big")
     return x
     b = 2
"""
FLIPPED = """--- a/m.py
+++ b/m.py
@@ -5,3 +5,3 @@ def ok(x):
     a = 1
-    return False
+    return True
     b = 2
"""
BENIGN = """--- a/m.py
+++ b/m.py
@@ -1,2 +1,3 @@
 def f(x):
+    \"\"\"Docstring.\"\"\"
     return x
"""


def review(diff):
    return reviewers.command_reviewer([sys.executable, EXAMPLE], timeout=30)(diff)


def test_flags_a_removed_guard_at_the_surviving_line():
    f = review(REMOVED_CHECK)
    assert [(x["file"], x["line"]) for x in f] == [("m.py", 11)]


def test_flags_a_weakened_return():
    assert [(x["file"], x["line"]) for x in review(FLIPPED)] == [("m.py", 6)]


def test_benign_diff_is_not_flagged():
    assert review(BENIGN) == []


@pytest.mark.parametrize("junk", ["", "not a diff at all\n", "@@ -1 +1 @@\n+x\n", "\x00\xff garbage"])
def test_junk_input_gives_an_empty_list_not_a_crash(junk):
    assert review(junk) == []


def test_exit_status_and_pure_json_on_stdout():
    p = subprocess.run([sys.executable, EXAMPLE], input=FLIPPED.encode(), capture_output=True, timeout=30)
    assert p.returncode == 0 and isinstance(json.loads(p.stdout), list) and p.stderr == b""


def test_runs_end_to_end_through_the_harness(capsys):
    assert cli.main(["run", "--reviewer", "command", "--json", "--command", sys.executable, EXAMPLE]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["overall"]["n"] >= 30
    assert 0 < data["overall"]["found"] < data["overall"]["n"]  # a toy: finds some, not all
