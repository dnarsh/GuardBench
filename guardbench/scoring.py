"""Scoring: recall per class/group, clean-twin alarm rate, precision, F1, Wilson 95% intervals."""
import math

from .defects import CLASSES, GROUPS
from .matcher import is_hit


def wilson(k, n, z=1.96):
    """Wilson score interval for k successes in n trials; (0, 1) when n == 0."""
    if not 0 <= k <= n:
        raise ValueError("need 0 <= k <= n, got k=%r n=%r" % (k, n))
    if n == 0:
        return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def newcombe_diff(k1, n1, k2, n2, z=1.96):
    """Newcombe hybrid score interval (method 10) for p1 - p2: (difference, lower, upper)."""
    if n1 <= 0 or n2 <= 0:
        raise ValueError("both groups need n > 0")
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    d = p1 - p2
    return (d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def h1_verdict(k, n, bound=0.75):
    """H1 (recall below `bound`): supported / refuted / inconclusive by the Wilson interval."""
    lo, hi = wilson(k, n)
    return "supported" if hi < bound else "refuted" if lo >= bound else "inconclusive"


def hypotheses(summary):
    """H1 on overall recall and H3 (guard minus logic) from a `run --json` summary."""
    o = summary["overall"]
    g, lg = summary["per_group"].get("guard"), summary["per_group"].get("logic")
    out = {"H1": {"recall": o["recall"], "ci": o["ci"], "verdict": h1_verdict(o["found"], o["n"])}}
    if g and lg:
        d, lo, hi = newcombe_diff(g["found"], g["n"], lg["found"], lg["n"])
        out["H3"] = {"diff": d, "ci": [lo, hi], "verdict": "supported" if lo > 0 or hi < 0 else "inconclusive"}
    return out


def _rate(k, n):
    return {"n": n, "found": k, "recall": k / n if n else None, "ci": wilson(k, n)}


def _comments(reviewer, diff):
    out = reviewer(diff)
    if not isinstance(out, list):
        raise ValueError("reviewer must return a list of comments, got %s" % type(out).__name__)
    return out


def run(defects, reviewer):
    """Run `reviewer` on every defect's bug diff and clean-twin diff and summarise."""
    if not defects:
        raise ValueError("no defects to score")
    tally = {c: [0, 0] for c in CLASSES}  # class -> [found, n]
    tp = total = alarms = 0
    for d in defects:
        bug = _comments(reviewer, d.bug_patch)
        clean = _comments(reviewer, d.clean_patch)
        hits = sum(is_hit(c, d.file, d.start, d.end) for c in bug)
        tally[d.cls][0] += hits > 0
        tally[d.cls][1] += 1
        tp += hits
        total += len(bug) + len(clean)
        alarms += len(clean) > 0
    found = sum(v[0] for v in tally.values())
    n = len(defects)
    groups = {}
    for cls, (f, m) in tally.items():
        g = groups.setdefault(GROUPS[cls], [0, 0])
        g[0] += f
        g[1] += m
    precision = tp / total if total else None
    recall = found / n
    f1 = 0.0
    if precision and recall:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "overall": _rate(found, n),
        "per_class": {c: _rate(*v) for c, v in tally.items() if v[1]},
        "per_group": {g: _rate(*v) for g, v in groups.items() if v[1]},
        "clean_alarm": {"n": n, "alarms": alarms, "rate": alarms / n, "ci": wilson(alarms, n)},
        "tp_comments": tp,
        "total_comments": total,
        "precision": precision,
        "f1": f1,
    }


def _fmt(r):
    lo, hi = r["ci"]
    rate = "n/a" if r["recall"] is None else "%.3f" % r["recall"]
    return "%s [%.3f, %.3f]  (%d/%d)" % (rate, lo, hi, r["found"], r["n"])


def format_report(s):
    lines = ["overall recall      " + _fmt(s["overall"])]
    lines += ["  group %-12s " % g + _fmt(r) for g, r in sorted(s["per_group"].items())]
    lines += ["  class %-18s " % c + _fmt(r) for c, r in s["per_class"].items()]
    a = s["clean_alarm"]
    lines.append("clean-twin alarms   %.3f [%.3f, %.3f]  (%d/%d)" % (
        a["rate"], a["ci"][0], a["ci"][1], a["alarms"], a["n"]))
    p = s["precision"]
    lines.append("precision           %s  (%d/%d comments)" % (
        "n/a" if p is None else "%.3f" % p, s["tp_comments"], s["total_comments"]))
    lines.append("F1                  %.3f" % s["f1"])
    return "\n".join(lines)
