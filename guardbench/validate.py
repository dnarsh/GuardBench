"""Defect validation: the app's test must pass on the clean app and clean twin, fail on the bug.

SECURITY MODEL (read before validating defects you did not write): this executes Python
code from the app, the patches and the test module. Hygiene only, NOT a sandbox:
the code runs in a throwaway copy of the app in a fresh temp dir, with a scrubbed
environment, no stdin, `python -E -s -B`, and a hard timeout. It can still read files
and use the network as your user. Patches are parsed strictly and cannot write outside
the copy. Validate only defects from sources you trust, ideally inside a container/VM.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from . import patch as P

MAX_OUTPUT = 4000
BROKEN = ("SyntaxError", "IndentationError", "ImportError", "ModuleNotFoundError")


def _copy_app(src, dst):
    for base, dirs, files in os.walk(src):
        for name in dirs + files:
            if os.path.islink(os.path.join(base, name)):
                raise ValueError("symlink in app: %s" % os.path.join(base, name))
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))


def _env(tmp):
    env = {k: tmp for k in ("TMP", "TEMP", "TMPDIR", "HOME", "USERPROFILE")}
    if os.environ.get("SYSTEMROOT"):  # Windows needs it to start Python
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return env


def run_tests(workdir, module, timeout):
    """Return (status, output); status is pass, fail, timeout or error (did not really run)."""
    cmd = [sys.executable, "-E", "-s", "-B", "-m", "unittest", "-q", module]
    try:
        p = subprocess.run(cmd, cwd=workdir, env=_env(workdir), stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout", ""
    out = p.stdout.decode("utf-8", "replace")[-MAX_OUTPUT:]
    ran = re.search(r"Ran (\d+) test", out)
    if p.returncode == 0:
        return ("pass" if ran and int(ran.group(1)) > 0 else "error"), out
    if not ran or int(ran.group(1)) == 0 or any(b in out for b in BROKEN):
        return "error", out
    return "fail", out


def validate_defect(d, timeout=60):
    """Return a list of problems; an empty list means the defect is valid."""
    problems = []
    test_file = d.test_module + ".py"
    with tempfile.TemporaryDirectory(prefix="guardbench-") as tmp:
        def fresh(name, diff=None):
            work = os.path.join(tmp, name)
            _copy_app(d.app_dir, work)
            if diff is not None:
                if any(p == test_file for p, _ in P.parse(diff)):
                    raise P.PatchError("patch may not edit the test module %s" % test_file)
                P.apply(work, diff)
            return work

        def check(label, name, diff, want):
            try:
                work = fresh(name, diff)
            except (P.PatchError, ValueError, OSError) as e:
                problems.append("%s: %s" % (label, e))
                return None
            status, out = run_tests(work, d.test_module, timeout)
            if status != want:
                if status == "timeout":
                    detail = "timed out after %ss" % timeout
                elif status in ("pass", "fail"):
                    detail = "did not %s" % want
                else:
                    detail = "did not run cleanly: " + out.strip()[-300:]
                problems.append("%s: tests %s" % (label, detail))
            return work

        check("clean app", "clean", None, "pass")
        bug_dir = check("bug patch", "bug", d.bug_patch, "fail")
        check("clean twin", "twin", d.clean_patch, "pass")
        if bug_dir is not None:
            try:
                touched = P.changed_lines(d.bug_patch).get(d.file, set())
                with open(os.path.join(bug_dir, *d.file.split("/")), encoding="utf-8") as fh:
                    size = len(fh.read().splitlines())
                if d.end > size or not touched & set(range(d.start, d.end + 1)):
                    problems.append("location %s:%d-%d does not overlap the bug patch changes %s (file has %d lines)"
                                    % (d.file, d.start, d.end, sorted(touched), size))
            except (P.PatchError, OSError) as e:
                problems.append("location: %s" % e)
    return problems
