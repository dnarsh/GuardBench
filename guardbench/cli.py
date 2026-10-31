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


def _source_paths(a, parser):
    """Resolve the effective source; a custom root always overrides the split."""
    if a.root:
        root, apps, split = a.root, a.apps or os.path.join(a.root, "apps"), "custom"
    elif a.split == "test":
        if not os.environ.get(HELDOUT_ENV):
            parser.error("--split test needs the %s environment variable (private test data)" % HELDOUT_ENV)
        root = os.environ[HELDOUT_ENV]
        apps, split = a.apps or os.path.join(REPO_ROOT, "apps"), "heldout"
    else:
        root, apps, split = REPO_ROOT, a.apps or os.path.join(REPO_ROOT, "apps"), "dev"
    return root, apps, split


def _load(a, parser):
    """Load the chosen source; held-out roots contain only defects/."""
    root, apps, _ = _source_paths(a, parser)
    return load_all(root, apps)


def _dataset_hashes(root, apps):
    return {"manifest": manifest_hash(root) if os.path.isdir(os.path.join(root, "defects")) else None,
            "apps_hash": tree_hash(apps) if os.path.isdir(apps) else None}


def _analysis_metadata(a, split, dataset, reviewer):
    transport = "callable" if ":" in a.reviewer else "command" if a.reviewer == "command" else "builtin"
    role = a.reviewer_role
    if transport == "builtin" or reviewer is reviewers.flag_every_hunk:
        role = "baseline"
    toy_module = sys.modules.get("examples.toy_reviewer")
    if toy_module is not None and reviewer is getattr(toy_module, "review", None):
        role = "toy"
    toy = os.path.normcase(os.path.realpath(os.path.join(REPO_ROOT, "examples", "toy_reviewer.py")))
    command = a.command or []
    toy_command = (any(os.path.normcase(os.path.realpath(arg)) == toy for arg in command)
                   or any(arg == "-m" and name == "examples.toy_reviewer" for arg, name in zip(command, command[1:])))
    if transport == "command" and toy_command:
        role = "toy"
    return {"schema_version": 1, "purpose": a.analysis_purpose, "split": split,
            "protocol": a.protocol, "dataset": dataset,
            "reviewer": {"label": a.reviewer, "role": role, "transport": transport}}


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
            p.add_argument("--analysis-purpose", choices=("pilot", "confirmatory"), default="pilot")
            p.add_argument("--reviewer-role", choices=("unknown", "model", "human"), default="unknown",
                           help="declared role, not authenticated; built-ins remain baselines")
            p.add_argument("--protocol", default="prereg-v3", help="registered analysis cohort identifier")
            p.add_argument("--reviewer-timeout", type=float, default=120)
            p.add_argument("--command", nargs=argparse.REMAINDER,
                           help="program and args for --reviewer command; must be the last option")
    p = sub.add_parser("hash")
    p.add_argument("directory")
    p.add_argument("--only", nargs="+", help="hash only these top-level entries of the directory")
    sub.add_parser("manifest").add_argument("directory")
    p = sub.add_parser("report", help="write docs/RESULTS.md from the baselines")
    p.add_argument("--root", help="directory holding defects/ for the dev split (default: this repo)")
    p.add_argument("--apps")
    p.add_argument("--heldout", help="held-out repo directory (default: $%s)" % HELDOUT_ENV)
    p.add_argument("--out", default=os.path.join(REPO_ROOT, "docs", "RESULTS.md"))
    p.add_argument("--no-toy", action="store_true", help="skip the examples/toy_reviewer.py row")
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
            try:
                result = hypotheses(json.load(fh))
            except ValueError as e:
                ap.error("invalid run summary: %s" % e)
            print(json.dumps(result, indent=2))
        return 0
    if a.cmd == "report":
        from .report import build
        dev = load_all(a.root or REPO_ROOT, a.apps)
        held_dir = a.heldout or os.environ.get(HELDOUT_ENV)
        held = load_all(held_dir, a.apps or os.path.join(REPO_ROOT, "apps")) if held_dir else None
        if not dev:
            print("no defects found", file=sys.stderr)
            return 1
        split_file = os.path.join(REPO_ROOT, "prereg", "split.sha256")
        with open(split_file, encoding="utf-8") as fh:
            want = fh.read().strip()
        text = build(dev, held or None, toy=not a.no_toy, split_hash=want,
                     manifest=manifest_hash(held_dir) if held else None)
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("wrote %s" % a.out)
        return 0
    if a.cmd == "build":
        from .build import write_items
        return write_items(a.specs, a.out, a.noise_dir, a.apps or os.path.join(REPO_ROOT, "apps"))
    source = _source_paths(a, ap)
    before = _dataset_hashes(*source[:2]) if a.cmd in ("run", "score") else None
    defects = load_all(*source[:2])
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
        reviewer = _reviewer(a, ap)
        summary = run(defects, reviewer)
    except reviewers.ReviewerError as e:
        print("reviewer error: %s" % e, file=sys.stderr)
        return 1
    if before != _dataset_hashes(*source[:2]):
        print("dataset changed during reviewer run; no summary emitted", file=sys.stderr)
        return 1
    summary["analysis"] = _analysis_metadata(a, source[2], before, reviewer)
    print(json.dumps(summary, indent=2) if a.json else format_report(summary))
    return 0
