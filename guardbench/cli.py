"""python -m guardbench validate|run|hyp|hash|manifest|build"""
import argparse
import importlib
import json
import os
import sys

from . import reviewers
from .defects import load_all, manifest_hash, tree_hash
from .baselines import baseline_report
from .scoring import format_report, hypotheses, run
from .validate import validate_defect

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELDOUT_ENV = "GUARDBENCH_HELDOUT"


def _load(a, parser):
    """Return the defects for the chosen split. The held-out split holds only defects/;
    its apps are the public ones (apps/ is frozen and covered by git)."""
    if a.root:
        return load_all(a.root, a.apps)
    if a.split == "test":
        if not os.environ.get(HELDOUT_ENV):
            parser.error("--split test needs the %s environment variable (private test data)" % HELDOUT_ENV)
        return load_all(os.environ[HELDOUT_ENV], a.apps or os.path.join(REPO_ROOT, "apps"))
    return load_all(REPO_ROOT, a.apps)


def _reviewer(a, parser):
    if ":" in a.reviewer:  # module:callable, runs the user's own code
        mod, _, attr = a.reviewer.partition(":")
        try:
            return getattr(importlib.import_module(mod), attr)
        except (ImportError, AttributeError) as e:
            parser.error("cannot load reviewer %r: %s" % (a.reviewer, e))
    try:
        return reviewers.get(a.reviewer, a.seed, a.command, a.reviewer_timeout)
    except reviewers.ReviewerError as e:
        parser.error(str(e))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="guardbench")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, aliases in (("validate", ()), ("run", ("score",)), ("baselines", ())):
        p = sub.add_parser(name, aliases=aliases)
        p.add_argument("--split", choices=("dev", "test"), default="dev")
        p.add_argument("--root", help="directory holding defects/ (and apps/); overrides --split")
        p.add_argument("--apps", help="apps directory (default: the public apps/ of this repo)")
        if name == "validate":
            p.add_argument("--timeout", type=float, default=60)
        elif name == "baselines":
            p.add_argument("--seeds", type=int, default=200)
        else:
            p.add_argument("--reviewer", required=True, help="hunk-all, random, command, or module:callable")
            p.add_argument("--seed", type=int, default=0)
            p.add_argument("--json", action="store_true")
            p.add_argument("--reviewer-timeout", type=float, default=120)
            p.add_argument("--command", nargs=argparse.REMAINDER,
                           help="program and args for --reviewer command; must be the last option")
    p = sub.add_parser("hash")
    p.add_argument("directory")
    p.add_argument("--only", nargs="+", help="hash only these top-level entries of the directory")
    sub.add_parser("manifest").add_argument("directory")
    p = sub.add_parser("hyp", help="H1 and H3 from the --json output of `run`")
    p.add_argument("summary", help="path to a `run --json` output file")
    p = sub.add_parser("build", help="compose defect specs with noise into items")
    p.add_argument("specs", nargs="+")
    p.add_argument("--out", required=True)
    p.add_argument("--noise-dir", default=os.path.join(REPO_ROOT, "noise"))
    p.add_argument("--apps")
    a = ap.parse_args(argv)

    if a.cmd == "hash":
        try:
            print(tree_hash(a.directory, a.only))
        except ValueError as e:
            ap.error(str(e))
        return 0
    if a.cmd == "manifest":
        print(manifest_hash(a.directory))
        return 0
    if a.cmd == "hyp":
        with open(a.summary, encoding="utf-8") as fh:
            print(json.dumps(hypotheses(json.load(fh)), indent=2))
        return 0
    if a.cmd == "build":
        from .build import write_items
        return write_items(a.specs, a.out, a.noise_dir, a.apps or os.path.join(REPO_ROOT, "apps"))
    defects = _load(a, ap)
    if not defects:
        print("no defects found", file=sys.stderr)
        return 1
    if a.cmd == "validate":
        bad = 0
        for d in defects:
            problems = validate_defect(d, a.timeout)
            bad += bool(problems)
            print("%s %s%s" % ("FAIL" if problems else "ok  ", d.id,
                               "".join("\n     - " + p for p in problems)))
        print("%d defect(s), %d invalid" % (len(defects), bad))
        return 1 if bad else 0
    if a.cmd == "baselines":
        print(baseline_report(defects, a.seeds))
        return 0
    try:
        summary = run(defects, _reviewer(a, ap))
    except reviewers.ReviewerError as e:
        print("reviewer error: %s" % e, file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2) if a.json else format_report(summary))
    return 0
