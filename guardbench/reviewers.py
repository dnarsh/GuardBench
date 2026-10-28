"""Reviewer adapters. A reviewer is a callable: diff text -> [{"file", "line", "text"}].

Built in: `hunk-all` (alias `flag-every-hunk`), `random`, `command` (shell out, see README).
No network, no keys, no model calls live here.
"""
import json
import subprocess
import sys

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


def command_reviewer(argv, timeout=120):
    """Run argv once per diff: diff on stdin (UTF-8), JSON findings on stdout (no shell)."""
    def review(diff):
        try:
            p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=(sys.platform != "win32"))
        except OSError as e:
            raise ReviewerError("cannot start %r: %s" % (argv[0], e))
        try:
            out, err = p.communicate(diff.encode("utf-8"), timeout=timeout)
        except subprocess.TimeoutExpired:
            kill_tree(p)
            p.communicate()
            raise ReviewerError("reviewer timed out after %ss" % timeout)
        except OSError:  # the command closed stdin without reading it
            out, err = p.communicate()
        finally:
            kill_tree(p)
        if p.returncode != 0:
            raise ReviewerError("reviewer exited with %s: %s" % (
                p.returncode, err.decode("utf-8", "replace")[-300:].strip()))
        if len(out) > MAX_STDOUT:
            raise ReviewerError("reviewer printed more than %d bytes" % MAX_STDOUT)
        try:
            raw = json.loads(out.decode("utf-8"))
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
