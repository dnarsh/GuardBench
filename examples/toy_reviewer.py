#!/usr/bin/env python3
"""TOY BASELINE. Not a real reviewer, not evidence about any model or tool.

Implements the GuardBench command-reviewer contract (docs/reviewers.md): a unified diff on stdin,
a JSON list of findings {"file", "line", "text"} on stdout, exit status 0.

The whole heuristic: in a block of removed/added lines, flag the block when it removes more
"guard-looking" lines than it adds (a `raise`, an `assert`, a `return False`, a lock, an
`if not`, a constant-time compare). A pure deletion is flagged at the next surviving line.
It reads only stdin, writes only stdout, opens no file and no socket, and starts no process, so it
is safe to run on diffs you do not trust (a diff is parsed as text, never executed).

    python -m guardbench run --reviewer command --command python examples/toy_reviewer.py
"""
import json
import re
import sys

GUARD = re.compile(r"\braise\b|\bassert\b|\breturn False\b|compare_digest|\block\b|\bif not\b|isinstance\(")
HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _guards(lines):
    return sum(1 for ln in lines if GUARD.search(ln))


def review(diff):
    findings, path = [], None
    lines = diff.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        i += 1
        if ln.startswith("+++ "):
            path = ln[4:].strip()
            path = path[2:] if path.startswith("b/") else path
            continue
        m = HUNK.match(ln)
        if not m or path is None:
            continue
        old_left, new_ln = int(m.group(1) or 1), int(m.group(2))
        new_left = int(m.group(3) or 1)
        removed, added, first_added = [], [], None

        def close(at):
            if removed and _guards(removed) > _guards(added):
                findings.append({"file": path, "line": first_added or at,
                                 "text": "toy heuristic: removes or weakens a guard"})
            removed.clear()
            added.clear()

        while i < len(lines) and (old_left > 0 or new_left > 0):
            body = lines[i]
            tag = body[:1]
            if tag == "-":
                removed.append(body[1:])
                old_left -= 1
            elif tag == "+":
                if not added:
                    first_added = new_ln
                added.append(body[1:])
                new_ln += 1
                new_left -= 1
            elif tag in (" ", ""):
                close(new_ln)
                first_added = None
                new_ln += 1
                old_left -= 1
                new_left -= 1
            elif tag == "\\":  # "\ No newline at end of file"
                pass
            else:
                break
            i += 1
        close(new_ln)
    return findings


def main():
    text = sys.stdin.buffer.read().decode("utf-8", "replace")
    json.dump(review(text), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
