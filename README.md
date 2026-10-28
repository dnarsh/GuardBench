# GuardBench

A public, judge-free benchmark of **seeded security-guard defects** for AI code reviewers.

Status: **work in progress, milestone 2.** The harness, 12 apps and 35 validated defect/clean-twin
pairs exist (20 public dev, 15 held out). No reviewer other than two trivial baselines has been run.
**No result about any model is claimed.** With only 15 held-out defects, pre-registered kill
criterion 1 (fewer than 100 test defects) applies: any run on the test split is a pilot.

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

| | apps | pairs | per class |
|---|---|---|---|
| public dev | 8 with items (12 apps ship) | 20 | 4 each |
| held out (private repo) | 4 (sessions, vault, jobq, pager) | 15 | 3 each |

The held-out split is not in this repo. Its manifest hash is in `prereg/split.sha256`
(`3343e5b8...`); its construction is described in the amendments.

## The honest numbers (dev split, no reviewer, baselines only)

`python -m guardbench baselines` on 20 dev items (min 8, mean 11.1, max 13 hunks per diff):

| Baseline | Recall | Precision | F1 | Clean-twin alarms |
|---|---|---|---|---|
| `random`, seed 0 (one run) | 0.100 [0.028, 0.301] (2/20) | n/a | n/a | n/a |
| `random`, exact expectation | 0.062 (over 200 seeds: mean 0.072, max 0.250) | | | |
| `hunk-all` | 1.000 [0.839, 1.000] (20/20) | 0.045 | 0.087 | 1.000 [0.839, 1.000] |

Milestone 1 had `random` at 10/10 on tiny diffs, which tripped kill criterion 3; how it was fixed is
in [`docs/noise-iteration.md`](docs/noise-iteration.md). `hunk-all` finds every defect by
construction and pays with precision and false alarms; recall alone does not discriminate it, which
is why F1 and the alarm rate are part of H2.

## What it is NOT

- Not a leaderboard and not evidence about any model.
- Not real-world vulnerabilities: the bugs are synthetic, written by one author (an AI agent).
- Not a sandbox. Validating a defect executes code (see Security model).
- Not large: 35 pairs, target 150+ held out.

## Honest limits

- **Small n.** 15 held-out items give very wide intervals; see the sample-size arithmetic.
- **Noise is cosmetic.** A reviewer that just finds the one behaviour-changing hunk gets most of the
  localisation for free. Noise of held-out apps is private; noise style is shared.
- **Contamination.** Apps, dev items, and the tests/READMEs of the held-out apps are public.
- **Dev share is 57%, not 40%** (10 pilot pairs were already public).
- **Tolerance** (+-3 lines) and the guard/logic grouping are judgement calls.
- Everything was authored and validated on Windows; CI runs Linux (Python 3.10, 3.12).

## Run it

Python 3.8+, standard library only. `pytest` is needed only for the harness tests.

```
python -m guardbench validate                    # prove every dev defect
python -m guardbench run --reviewer random       # hunk-all, random, command, or module:callable
python -m guardbench baselines                   # both baselines with exact random expectation
python -m guardbench hyp run.json                # H1 verdict and H3 interval from `run --json`
python -m guardbench manifest DIR                # manifest hash used for prereg/split.sha256
python -m pytest -q
```

Reviewer interface (callable or external command with JSON on stdout): [`docs/reviewers.md`](docs/reviewers.md).
No API keys and no model calls exist in this repository.

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
ideally in a container or VM. Written review: [`docs/reviews/validator-and-sandbox.md`](docs/reviews/validator-and-sandbox.md).
A `command` reviewer is user code and is not sandboxed at all.

## Design decisions made without asking

- Items are built, not hand-edited: `specs/` (defect edits) plus `noise/` (benign pools) go through
  `guardbench build`, which refuses outputs outside 8-25 hunks and 3-6 files.
- The split is by app so noise cannot be subtracted from held-out items.
- App tests use `unittest`; races are deterministic with a hook and a timed barrier.
- A pure deletion has no added line, so its location is the two surviving lines around it.

## Contributing, provenance, license

[CONTRIBUTING.md](CONTRIBUTING.md), [PROVENANCE.md](PROVENANCE.md). MIT, see [LICENSE](LICENSE).
