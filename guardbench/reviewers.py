"""Reviewer adapters. A reviewer is a callable: diff text -> [{"file", "line", "text"}].

Built in: `hunk-all` (alias `flag-every-hunk`), `random`, `command` (shell out, see README).
No network, no keys, no model calls live here.
"""
import json
import subprocess
import sys
import threading
import time

from .baselines import flag_every_hunk, make_random
from .validate import kill_tree

MAX_STDOUT = 1024 * 1024


class ReviewerError(RuntimeError):
    pass


def _findings(raw):
    if isinstance(raw, dict):
        raw = raw.get("findings")
    if not isinstance(raw, list):
        raise ReviewerError("output must be a JSON list of findings or {\"findings\": [...]}")
    out = []
    for f in raw:
        if not isinstance(f, dict) or not isinstance(f.get("file"), str):
            raise ReviewerError("each finding needs a string \"file\": %r" % (f,))
        line = f.get("line")
        if isinstance(line, bool) or not isinstance(line, int) or line < 1:
            raise ReviewerError("each finding needs an integer \"line\" >= 1: %r" % (f,))
        text = f.get("text", "")
        out.append({"file": f["file"], "line": line, "text": text if isinstance(text, str) else str(text)})
    return out


def _pump(p, stream, keep, over, cap):
    """Read `stream` in chunks. keep > 0: retain only the last `keep` bytes (stderr).
    keep == 0: retain everything but stop and kill the process once more than `cap` bytes arrive."""
    buf = bytearray()
    while True:
        chunk = stream.read1(65536)
        if not chunk:
            return buf
        buf.extend(chunk)
        if keep:
            del buf[:-keep]
        elif len(buf) > cap:
            over.set()
            kill_tree(p)
            return buf


def command_reviewer(argv, timeout=120):
    """Run argv once per diff: diff on stdin (UTF-8), JSON findings on stdout (no shell).

    stdout is read as a stream and the process is killed the moment it exceeds MAX_STDOUT bytes;
    stderr keeps only its last 4000 bytes, so neither stream can grow without bound.
    """
    def review(diff):
        try:
            p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=(sys.platform != "win32"))
        except OSError as e:
            raise ReviewerError("cannot start %r: %s" % (argv[0], e))
        over, res = threading.Event(), {}

        def feed():
            try:
                p.stdin.write(diff.encode("utf-8"))
            except OSError:  # the command closed stdin without reading it
                pass
            try:
                p.stdin.close()
            except OSError:
                pass

        threads = [threading.Thread(target=feed, daemon=True),
                   threading.Thread(target=lambda: res.update(out=_pump(p, p.stdout, 0, over, MAX_STDOUT)), daemon=True),
                   threading.Thread(target=lambda: res.update(err=_pump(p, p.stderr, 4000, over, 0)), daemon=True)]
        for th in threads:
            th.start()
        deadline = time.monotonic() + timeout
        stuck = False
        try:
            try:
                p.wait(timeout)
            except subprocess.TimeoutExpired:
                raise ReviewerError("reviewer timed out after %ss" % timeout)
        finally:
            kill_tree(p)
            p.wait()
            for th in threads[1:]:  # a grandchild may keep the pipes open after the parent is gone
                th.join(max(deadline - time.monotonic(), 0.5))
            stuck = any(th.is_alive() for th in threads[1:])
            if not stuck:  # closing a pipe a reader is still blocked on would hang
                for s in (p.stdout, p.stderr):
                    s.close()
        if stuck:
            raise ReviewerError("reviewer left a process holding its output open")
        if over.is_set():
            raise ReviewerError("reviewer printed more than %d bytes" % MAX_STDOUT)
        if p.returncode != 0:
            raise ReviewerError("reviewer exited with %s: %s" % (
                p.returncode, bytes(res.get("err", b"")).decode("utf-8", "replace")[-300:].strip()))
        try:
            raw = json.loads(bytes(res.get("out", b"")).decode("utf-8"))
        except ValueError as e:
            raise ReviewerError("reviewer output is not valid JSON: %s" % e)
        return _findings(raw)
    return review


def get(name, seed=0, command=None, timeout=120):
    if name in ("hunk-all", "flag-every-hunk"):
        return flag_every_hunk
    if name == "random":
        return make_random(seed)
    if name == "command":
        if not command:
            raise ReviewerError("--reviewer command needs --command PROGRAM [ARGS...]")
        return command_reviewer(list(command), timeout)
    raise ReviewerError("unknown reviewer %r (hunk-all, random, command)" % name)
