"""Trivial reference reviewers. A reviewer is any callable: diff text -> [{file, line, text}]."""
import random
import zlib

from .matcher import TOLERANCE
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


def random_hit_probability(diff, file, start, end, tol=TOLERANCE):
    """Exact chance that the `random` baseline hits [start, end] in this diff."""
    try:
        lines = new_side_lines(diff)
    except PatchError:
        return 0.0
    hit = sum(1 for p, n in lines if p == file and start - tol <= n <= end + tol)
    return hit / len(lines) if lines else 0.0


def baseline_report(defects, seeds=200):
    """Text table for the two pre-registered baselines on `defects`."""
    from .scoring import run
    hunks = [len(anchors(d.bug_patch)) for d in defects]
    p = [random_hit_probability(d.bug_patch, d.file, d.start, d.end) for d in defects]
    recalls = sorted(run(defects, make_random(s))["overall"]["found"] / len(defects) for s in range(seeds))
    ha = run(defects, flag_every_hunk)
    lo, hi = recalls[int(0.025 * (seeds - 1))], recalls[int(round(0.975 * (seeds - 1)))]
    return "\n".join([
        "defects %d, hunks per bug diff: min %d, mean %.1f, max %d" % (
            len(defects), min(hunks), sum(hunks) / len(hunks), max(hunks)),
        "hunk-all recall %.3f [%.3f, %.3f] precision %.3f F1 %.3f clean alarms %.3f" % (
            ha["overall"]["recall"], ha["overall"]["ci"][0], ha["overall"]["ci"][1],
            ha["precision"] or 0.0, ha["f1"], ha["clean_alarm"]["rate"]),
        "random expected recall %.3f (exact, mean hit probability per diff)" % (sum(p) / len(p)),
        "random over %d seeds: mean recall %.3f, 2.5%%-97.5%% of runs %.3f-%.3f, max %.3f" % (
            seeds, sum(recalls) / seeds, lo, hi, recalls[-1]),
    ])
