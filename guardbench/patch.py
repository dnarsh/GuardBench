"""Strict unified-diff parser and applier for existing text files (stdlib only).

Only `--- a/P` / `+++ b/P` modifications of files that already exist are accepted.
Renames, creations, deletions, "\\ No newline" markers and fuzzy matching are rejected.
"""
import os
import re
from collections import namedtuple

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
Hunk = namedtuple("Hunk", "old_start old_len new_start new_len lines")


class PatchError(ValueError):
    pass


def _path(raw, prefix):
    p = raw.split("\t")[0].rstrip("\r")
    if not p.startswith(prefix):
        raise PatchError("path must start with %r: %r" % (prefix, p))
    p = p[len(prefix):]
    parts = p.split("/")
    if (not p or "\x00" in p or "\\" in p or ":" in p or p.startswith("/")
            or any(s in ("", ".", "..") for s in parts)):
        raise PatchError("unsafe path in patch: %r" % p)
    return p


def parse(text):
    """Return [(path, [Hunk, ...]), ...]; raise PatchError on anything unexpected."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    files, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith(("diff ", "index ")):
            i += 1
            continue
        if not ln.startswith("--- ") or i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
            raise PatchError("unexpected line %d: %r" % (i + 1, ln[:60]))
        old, new = _path(ln[4:], "a/"), _path(lines[i + 1][4:], "b/")
        if old != new:
            raise PatchError("rename not supported: %s -> %s" % (old, new))
        i += 2
        hunks = []
        while i < len(lines) and lines[i].startswith("@@"):
            m = HUNK_RE.match(lines[i])
            if not m:
                raise PatchError("bad hunk header: %r" % lines[i])
            os_, ol, ns, nl = (int(g) if g is not None else 1 for g in m.groups())
            i += 1
            body, o, n = [], ol, nl
            while o > 0 or n > 0:
                if i >= len(lines) or not lines[i][:1] in (" ", "+", "-"):
                    raise PatchError("hunk body does not match its header counts")
                tag = lines[i][0]
                o -= tag != "+"
                n -= tag != "-"
                body.append((tag, lines[i][1:]))
                i += 1
            if o < 0 or n < 0:
                raise PatchError("hunk body does not match its header counts")
            hunks.append(Hunk(os_, ol, ns, nl, body))
        if not hunks:
            raise PatchError("no hunks for %s" % old)
        files.append((old, hunks))
    if not files:
        raise PatchError("empty patch")
    return files


def apply(root, text):
    """Apply the patch inside `root`. Validates everything before writing anything."""
    root_real = os.path.realpath(root)
    staged = []
    for path, hunks in parse(text):
        target = os.path.realpath(os.path.join(root_real, *path.split("/")))
        if os.path.commonpath([root_real, target]) != root_real:
            raise PatchError("path escapes root: %s" % path)
        if not os.path.isfile(target):
            raise PatchError("no such file: %s" % path)
        with open(target, encoding="utf-8", newline=None) as fh:
            src = fh.read().split("\n")
        out, cur = [], 0
        for h in hunks:
            pos = h.old_start - 1 if h.old_len else h.old_start
            old = [t for tag, t in h.lines if tag != "+"]
            if pos < cur or src[pos:pos + len(old)] != old:
                raise PatchError("context mismatch in %s at line %d" % (path, h.old_start))
            out += src[cur:pos] + [t for tag, t in h.lines if tag != "-"]
            cur = pos + len(old)
        staged.append((target, "\n".join(out + src[cur:])))
    for target, data in staged:
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(data)


def _walk(text):
    """Yield (path, hunk, tag, n): n is the new-side line number (for '-', the next new line)."""
    for path, hunks in parse(text):
        for h in hunks:
            n = h.new_start if h.new_len else h.new_start + 1
            for tag, _ in h.lines:
                yield path, h, tag, n
                if tag != "-":
                    n += 1


def _hunk_changed(text):
    """Yield (path, sorted new-side lines a reviewer could anchor a comment to) per hunk.

    Added lines count; a pure deletion (no added line in the same run) counts as the
    two surviving lines around it.
    """
    acc, run = {}, None  # run = [adds, first new line seen in the run]

    def flush(key):
        if run and run[0]:
            acc.setdefault(key, set()).update(run[0])
        elif run:
            acc.setdefault(key, set()).update(x for x in (run[1] - 1, run[1]) if x >= 1)

    key = None
    for path, h, tag, n in _walk(text):
        k = (path, h.old_start, h.new_start)
        if k != key:
            flush(key)
            key, run = k, None
        if tag == " ":
            flush(key)
            run = None
            continue
        run = run or [set(), n]
        if tag == "+":
            run[0].add(n)
    flush(key)
    for (path, _, _), s in acc.items():
        yield path, sorted(s)


def changed_lines(text):
    """{path: {new-side lines added, plus both neighbours of every deletion}}."""
    out = {}
    for path, s in _hunk_changed(text):
        out.setdefault(path, set()).update(s)
    return out


def anchors(text):
    """One (path, first changed new-side line) per hunk."""
    return [(path, s[0]) for path, s in _hunk_changed(text) if s]


def new_side_lines(text):
    """Every (path, line) shown on the new side of the diff, context included."""
    return [(path, n) for path, _, tag, n in _walk(text) if tag != "-"]
