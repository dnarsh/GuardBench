# GuardBench

A public, judge-free benchmark of **seeded security-guard defects** for AI code reviewers.

Status: **work in progress, foundation milestone (week 1).** The harness works; the dataset is a
10-pair pilot. No reviewer has been run on anything yet. No result is claimed.

## What it is

Each defect is a unified diff that plants one flaw in a small Python app, plus:

- a unit test that passes on the clean app and **fails** on the buggy app (proof the defect is real),
- a ground-truth location (file + line range in the patched file),
- a **clean twin**: a same-shaped diff to the same region without the flaw, to measure false alarms.

Five classes: fail-open guard, removed validation, secret leakage (the "guard" group), race
condition and off-by-one (the "logic" group). The claim under test, pre-registered in
[`prereg/PREREGISTRATION.md`](prereg/PREREGISTRATION.md): reviewers miss guard defects at a measurable
rate that differs from logic defects.

Scoring needs no judge model: a reviewer comment is a hit if it names the right file and lands within
+-3 lines of the planted range. Reported: recall per class and group, clean-twin alarm rate,
precision, F1, all with Wilson 95% intervals. Baselines: `flag-every-hunk` and `random`.

## What it is NOT

- Not a leaderboard and not evidence about any model yet.
- Not a collection of real-world vulnerabilities; the bugs are synthetic.
- Not a sandbox. Validating a defect executes code (see Security model).
- Not a large benchmark: 5 apps, 10 pairs today. Target is 150+ held-out defects.

## Honest limits

- **Synthetic bugs** written by one author (an AI agent, directed and reviewed by the owner).
- **Small n.** With 10 pairs every interval is huge (a perfect 10/10 still has a Wilson lower
  bound of 0.72). See the sample-size arithmetic in the pre-registration.
- **Contamination.** The apps and dev defects are public and may end up in training data. The
  test split is meant to stay private (see below).
- **Localisation is too easy right now.** Diffs are tiny, so even the `random` baseline finds
  10/10 dev defects. That already trips pre-registered kill criterion 3 (random finds more than
  70%). The test split must use larger, multi-hunk diffs before any reviewer is run on it; until
  then recall mostly measures "commented at all". The clean-twin alarm rate and precision are the
  informative numbers today.
- **Location tolerance** (+-3 lines) and the guard/logic grouping are judgement calls.

## Run it

Python 3.8+, standard library only. `pytest` is needed only for the harness tests.

```
python -m guardbench validate                  # run every defect's proof on the dev set
python -m guardbench score --reviewer random   # or flag-every-hunk, or pkg.module:callable
python -m guardbench hash DIR                  # tree hash used for prereg/split.sha256
python -m pytest -q
```

A reviewer is any callable `diff_text -> list of {"file": str, "line": int, "text": str}`
(file is the path without `a/` or `b/`; line is a new-side line number). The harness makes no
API calls and holds no keys; wrapping a model is the next milestone.

### Private test split

The test defects are never committed here. Put them in a directory with the same layout
(`apps/` and `defects/`) and point the harness at it:

```
GUARDBENCH_TEST_DIR=/path/to/private python -m guardbench score --split test --reviewer ...
```

Its tree hash is committed to `prereg/split.sha256` before any reviewer runs on it (rules in the
pre-registration).

## Security model

`validate` runs Python code from the app, the patches and the test module. It does this in a throwaway
copy, in a fresh temp directory, with a scrubbed environment, `python -E -s -B`, no stdin and a hard
timeout. Patches are parsed strictly: only edits to existing files, no `..`, absolute or
backslash paths, no symlink escapes, no edits to the test module. This is hygiene, **not a
sandbox**: the code can still read your files and use the network, and on a timeout only the direct
child process is killed. Validate defects only from sources you trust, ideally inside a container or VM.

## Design decisions made without asking

- App tests use `unittest` so apps need no dependencies; pytest runs only the harness tests.
- Race-condition defects are made deterministic with a `_checkpoint()` hook and a barrier with a
  0.5 s timeout, not with sleeps or luck.
- A pure deletion (removed validation) has no added line, so its location is the two surviving
  lines around the hole.
- All 10 pairs are currently in the public dev set; the 60% test split is a later milestone.
- A clean twin's comments are all false alarms; precision counts them.

## Add a defect

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Provenance and license

See [PROVENANCE.md](PROVENANCE.md). MIT, see [LICENSE](LICENSE).
