"""Trivial reference reviewers. A reviewer is any callable: diff text -> [{file, line, text}]."""
import random
import zlib

from .patch import PatchError, anchors, new_side_lines


def flag_every_hunk(diff):
    try:
        return [{"file": p, "line": n, "text": "flagged hunk"} for p, n in anchors(diff)]
    except PatchError:
        return []


def make_random(seed=0):
    """One comment on a uniformly random new-side line; deterministic per (seed, diff)."""
    def random_reviewer(diff):
        try:
            lines = new_side_lines(diff)
        except PatchError:
            return []
        if not lines:
            return []
        path, n = random.Random("%d:%d" % (seed, zlib.crc32(diff.encode()))).choice(lines)
        return [{"file": path, "line": n, "text": "random line"}]
    return random_reviewer
