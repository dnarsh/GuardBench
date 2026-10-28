"""Defect validation: the app's test must pass on the clean app and clean twin, fail on the bug.

SECURITY MODEL (read before validating defects you did not write): this executes Python
code from the app, the patches and the test module. It is hygiene, NOT a sandbox.

What it does: a throwaway copy of the app in a fresh temp dir; a scrubbed environment (only
what Python needs to start, plus TMP/HOME pointing at a private temp dir); no stdin;
`python -E -s -B`; a hard timeout that kills the whole process tree (process group on POSIX,
`taskkill /T` on Windows), also after a normal exit so stray children cannot linger; output
read through a pipe and capped (only the tail is kept, the run is killed past MAX_TOTAL
bytes); and a Python-level block on outgoing sockets (connect, create_connection, DNS).

What it does NOT do: it is no container. The code still runs as your user and can read
and write any file you can, and can start programs. The network block is a monkey-patch,
so ctypes, subprocess (curl) or `_socket` get around it. A process that leaves the process
group (POSIX setsid) or is re-parented after its parent exits (Windows) can outlive the
kill. There is no memory or CPU limit. Validate only defects from sources you trust,
ideally inside a container or VM.
"""
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading

from . import patch as P

MAX_OUTPUT = 4000  # tail kept for reports
MAX_TOTAL = 4 * 1024 * 1024  # bytes of output before the run is killed
BROKEN = ("SyntaxError", "IndentationError", "ImportError", "ModuleNotFoundError")
# Runs the test module with outgoing network calls turned into errors.
BOOT = ("import socket, sys, unittest\n"
        "def deny(*a, **k):\n    raise OSError('network disabled by guardbench')\n"
        "for n in ('connect', 'connect_ex'):\n    setattr(socket.socket, n, deny)\n"
        "for n in ('create_connection', 'getaddrinfo', 'gethostbyname', 'gethostbyname_ex'):\n"
        "    setattr(socket, n, deny)\n"
        "unittest.main(module=None, argv=['unittest', '-q', sys.argv[1]])\n")


def _copy_app(src, dst):
    for base, dirs, files in os.walk(src):
        for name in dirs + files:
            if os.path.islink(os.path.join(base, name)):
                raise ValueError("symlink in app: %s" % os.path.join(base, name))
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))


def _env(home):
    env = {k: home for k in ("TMP", "TEMP", "TMPDIR", "HOME", "USERPROFILE")}
    if os.environ.get("SYSTEMROOT"):  # Windows needs it to start Python
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return env


def kill_tree(p):
    """Kill p and every descendant that is still attached to it."""
    if os.name == "nt":
        tk = os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), "System32", "taskkill.exe")
        subprocess.run([tk, "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
    try:
        p.kill()
    except OSError:
        pass


def run_tests(workdir, module, timeout):
    """Return (status, output); status is pass, fail, timeout or error (did not really run)."""
    home = tempfile.mkdtemp(prefix="guardbench-home-")
    tail, seen, over = bytearray(), [0], threading.Event()
    try:
        p = subprocess.Popen([sys.executable, "-E", "-s", "-B", "-c", BOOT, module], cwd=workdir,
                             env=_env(home), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=(os.name != "nt"))

        def pump():
            while True:
                b = p.stdout.read1(65536)
                if not b:
                    return
                seen[0] += len(b)
                tail.extend(b)
                del tail[:-MAX_OUTPUT]
                if seen[0] > MAX_TOTAL:
                    over.set()
                    kill_tree(p)
                    return

        reader = threading.Thread(target=pump, daemon=True)
        reader.start()
        timed_out = False
        try:
            p.wait(timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        kill_tree(p)  # also after a normal exit: leftovers must not outlive the run
        p.wait()
        reader.join(5)
        p.stdout.close()
    finally:
        shutil.rmtree(home, ignore_errors=True)
    out = bytes(tail).decode("utf-8", "replace")
    if over.is_set():
        return "error", "output limit exceeded (%d bytes)\n%s" % (MAX_TOTAL, out)
    if timed_out:
        return "timeout", ""
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
