# GuardBench

A public, judge-free benchmark of **seeded security-guard defects** for AI code reviewers.

Status: **v0.2.0, work in progress, milestone 3.** The harness, 20 small apps and 130 validated
defect/clean-twin pairs exist (30 public dev, 100 held out). No reviewer other than two trivial
baselines and one labelled toy script has been run. **No result about any model is claimed, and no
hypothesis (H1, H2, H3) has a verdict.** The pre-registered held-out target is 150 defects, so any
run on the current 100 is a pilot. Numbers: [`docs/RESULTS.md`](docs/RESULTS.md).

## What it is

Each item is a realistic review unit: a unified diff of 8 to 25 hunks over 3 to 6 files in a small
Python app, where **one hunk** plants a flaw and the rest are benign changes (docs, renames,
refactors, logging-style edits). Each item has:

- a unit test that passes on the clean app and **fails** on the buggy app (proof the defect is real),
- a ground-truth location (file + line range in the patched file),
- a **clean twin**: the same benign hunks with a non-buggy version of the defect hunk, to measure
  false alarms.

Five classes: fail-open guard, removed validation, secret leakage (the "guard" group), race
condition and off-by-one (the "logic" group). Claim under test, pre-registered in
[`prereg/PREREGISTRATION.md`](prereg/PREREGISTRATION.md) and amended in
[`prereg/AMENDMENTS.md`](prereg/AMENDMENTS.md): reviewers miss guard defects at a measurable rate
that differs from logic defects.

Scoring needs no judge model: a comment is a hit if it names the right file and lands within +-3
lines of the planted range. Reported: recall per class and group, clean-twin alarm rate, precision,
F1, with Wilson 95% intervals; `guardbench hyp` adds the H1 verdict and the H3 Newcombe interval.

## Data

| | apps with items | pairs | per class |
|---|---|---|---|
| public dev | 9 (of 20 apps that ship) | 30 | 6 each |
| held out (private repo) | 11 | 100 | 20 each |

The held-out items are not in this repo. Their manifest hash is in `prereg/split.sha256`
(`ae29a20e...`); how they were built and the order of operations are in the amendments (A6 to A9).
The original 12 apps are byte-for-byte unchanged since `prereg-v2` (checked by a test); apps 13 to 20
were added in new directories only.

## The honest numbers (baselines only, no model)

Full tables with Wilson intervals, per-class recall and Newcombe differences:
[`docs/RESULTS.md`](docs/RESULTS.md) (regenerate with `python -m guardbench report`).

| Reviewer | Dev recall (n=30) | Held-out recall (n=100) | Clean-twin alarm (held-out) |
|---|---|---|---|
| `random` (seed 0, one run; exact expectation 0.064 dev, 0.059 held-out) | 0.133 | 0.050 | 1.000 |
| `hunk-all` | 1.000 | 1.000 | 1.000 (precision 0.045) |
| `examples/toy_reviewer.py` (toy heuristic) | 0.500 | 0.520 | 0.110 (precision 0.825) |

What these mean, and do not mean: `hunk-all` finds everything by construction and is useless
(precision 0.045). `random` shows the localisation floor is low. The **toy** script, which only looks for
a removed `raise` or a flipped `return False`, finds half the defects (all of removed-validation and
nearly all fail-open, none of secret-leakage or off-by-one): that is a measure of how much of the
benchmark is solvable through planted-bug style artifacts, not a result about reviewers. Any real
reviewer's recall must be read against it.

## What it is NOT

- Not a leaderboard and not evidence about any model.
- Not real-world vulnerabilities: the bugs are synthetic, written by one author (an AI agent).
- Not a sandbox. Validating a defect executes code (see Security model).
- Not large: 130 pairs; the pre-registered held-out target is 150.

## Honest limits

- **Small n.** 100 held-out items still give wide intervals, and per-class cells (20) wider.
- **Planted-bug style artifacts.** Defects are small edits (a flipped return, a deleted `raise`).
  The toy script exploits this. The 8 apps added in milestone 3 are uniform in style.
- **Noise is cosmetic.** Noise of the new apps is one-line docstrings from the public
  `tools/gen_noise.py`, so it is reproducible by anyone; docstring-only hunks are an obvious thing to
  ignore. Noise pools of the milestone-2 held-out apps remain private.
- **Contamination.** Apps, dev items and the tests/READMEs of the held-out apps are public, and
  those tests and READMEs name the rule each defect breaks.
- **Dev share is 23%, not 40%.**
- **Tolerance** (+-3 lines) and the guard/logic grouping are judgement calls.
- **Self-review.** The written reviews are by the agent that wrote the code.
- Everything was authored and validated on Windows; CI runs Linux (Python 3.10, 3.12).

## Run it

Python 3.8+, standard library only. `pytest` is needed only for the harness tests.

```
python -m guardbench validate                    # prove every dev defect
python -m guardbench run --reviewer random       # hunk-all, random, command, or module:callable
python -m guardbench run --reviewer command --command python examples/toy_reviewer.py
python -m guardbench baselines                   # both baselines with exact random expectation
python -m guardbench report                      # writes docs/RESULTS.md (held-out needs GUARDBENCH_HELDOUT)
python -m guardbench hyp run.json                # H1 verdict and H3 interval from `run --json`
python -m guardbench manifest DIR                # manifest hash used for prereg/split.sha256
python -m guardbench hash apps --only NAME ...   # hash of selected apps (the original 12 are frozen)
python -m pytest -q
```

Reviewer interface (callable or external command with JSON on stdout): [`docs/reviewers.md`](docs/reviewers.md).
[`examples/toy_reviewer.py`](examples/toy_reviewer.py) implements it with a 40-line heuristic, **a toy
baseline, not a tool**. No API keys and no model calls exist in this repository.

### Held-out split

Clone the private repo and set `GUARDBENCH_HELDOUT` to it; only its `defects/` directory is read, and
apps come from this repo's `apps/`:

```
GUARDBENCH_HELDOUT=/path/to/GuardBench-heldout python -m guardbench validate --split test
```

## Security model

`validate` runs Python from the app, patches and test module. Controls: throwaway copy in a temp dir,
scrubbed environment with a private temp HOME, no stdin, `python -E -s -B`, hard timeout that kills
the whole process tree (POSIX process group, Windows `taskkill /T`), output capped at 4 MiB, outgoing
sockets blocked by a Python-level patch. Not covered: it runs as your user and can read your files;
the network block is bypassable (ctypes, curl); a process that escapes its group or is re-parented
can outlive the kill; no CPU, memory or disk limit. Validate defects only from sources you trust,
ideally in a container or VM. Written reviews: [`docs/reviews/`](docs/reviews/).
A `command` reviewer is user code and is not sandboxed at all; the harness streams its output with a
hard 1 MiB cap and bounded stderr, and fails (rather than hangs) if it leaves a process holding the pipe.

## Design decisions made without asking

- Items are built, not hand-edited: `specs/` (defect edits) plus `noise/` (benign pools) go through
  `guardbench build`, which refuses outputs outside 8-25 hunks and 3-6 files.
- The split is by app so noise cannot be subtracted from held-out items.
- App tests use `unittest`; races are deterministic with a hook and a timed barrier.
- A pure deletion has no added line, so its location is the two surviving lines around it.
- New apps are added in new directories so the milestone-2 held-out items stay valid (amendment A6).

## Contributing, provenance, license

[CONTRIBUTING.md](CONTRIBUTING.md), [PROVENANCE.md](PROVENANCE.md), [CHANGELOG.md](CHANGELOG.md).
MIT, see [LICENSE](LICENSE).
