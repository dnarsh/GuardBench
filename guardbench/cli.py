"""python -m guardbench validate|score|hash"""
import argparse
import importlib
import json
import os
import sys

from .baselines import flag_every_hunk, make_random
from .defects import load_all, tree_hash
from .scoring import format_report, run
from .validate import validate_defect

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_ENV = "GUARDBENCH_TEST_DIR"


def _root(a, parser):
    if a.root:
        return a.root
    if a.split == "test":
        if not os.environ.get(TEST_ENV):
            parser.error("--split test needs the %s environment variable (private test data)" % TEST_ENV)
        return os.environ[TEST_ENV]
    return REPO_ROOT


def _reviewer(a, parser):
    if a.reviewer == "flag-every-hunk":
        return flag_every_hunk
    if a.reviewer == "random":
        return make_random(a.seed)
    mod, _, attr = a.reviewer.partition(":")
    if not attr:
        parser.error("reviewer must be flag-every-hunk, random or module:callable")
    try:
        return getattr(importlib.import_module(mod), attr)  # runs the user's own code
    except (ImportError, AttributeError) as e:
        parser.error("cannot load reviewer %r: %s" % (a.reviewer, e))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="guardbench")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "score"):
        p = sub.add_parser(name)
        p.add_argument("--split", choices=("dev", "test"), default="dev")
        p.add_argument("--root", help="directory holding apps/ and defects/ (overrides --split)")
        if name == "validate":
            p.add_argument("--timeout", type=float, default=60)
        else:
            p.add_argument("--reviewer", required=True)
            p.add_argument("--seed", type=int, default=0)
            p.add_argument("--json", action="store_true")
    sub.add_parser("hash").add_argument("directory")
    a = ap.parse_args(argv)

    if a.cmd == "hash":
        print(tree_hash(a.directory))
        return 0
    defects = load_all(_root(a, ap))
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
    summary = run(defects, _reviewer(a, ap))
    print(json.dumps(summary, indent=2) if a.json else format_report(summary))
    return 0
