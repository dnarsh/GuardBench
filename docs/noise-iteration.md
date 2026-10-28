# Making the review units realistic (kill criterion 3)

Pre-registered kill criterion 3: if the `random` baseline finds more than 70% of defects,
localisation is too easy and the design must change before any reviewer is run.

## Iteration 0: milestone 1 (tiny diffs)

Each bug diff was one hunk of about 7 lines in one file. Result on the 10 dev pairs: `random`
(seed 0) found 10/10, Wilson 95% [0.722, 1.000]. Kill criterion 3 was tripped on dev. No reviewer
had been run, so nothing was invalidated.

## Iteration 1: multi-hunk items (this milestone)

Every item is now a composition: one seeded defect hunk plus benign noise hunks (docstring and
comment edits, renames of locals, loops rewritten as comprehensions and back, logging-style
refactors, constant extraction, README edits). The noise is applied identically to the bug diff
and the clean twin, so the defect hunk is the only difference between them. Rules, all enforced:
8 to 25 hunks and 3 to 6 files per diff; noise stays at least 8 lines from the defect so hunks
never merge; the app's tests still pass with all noise applied (`tests/test_noise.py`) and each
item still validates (passes clean and twin, fails on the bug).

To carry the noise the five milestone-1 apps were grown (two helper modules and a README each,
with tests), which moves every line number; the 10 original items were rebuilt from their
original edits.

Result on the 20-item dev split (`python -m guardbench baselines`):

| Baseline | Result |
|----------|--------|
| hunks per bug diff | min 8, mean 11.1, max 13 |
| random, exact expected recall | 0.062 (mean over items of hit lines / lines shown) |
| random, 200 seeds | mean 0.072, 95% of runs between 0.000 and 0.200, max 0.250 |
| random, seed 0 | see README for the run with its Wilson interval |
| hunk-all | recall 1.000 [0.839, 1.000], precision 0.045, F1 0.087, clean-twin alarms 1.000 |

Kill criterion 3 is no longer tripped: expected `random` recall is about 6%, against a 70% limit.

`hunk-all` still has recall 1.0. That is by construction (it comments on every hunk, so it always
lands on the defect hunk) and the benchmark does not hide it; what changed is that its precision
fell from about 0.5 to 0.045 and its F1 to 0.087, so it is far from the ceiling on the metrics that
matter (precision, F1, clean-twin alarm rate). Hypothesis H2 compares F1 and alarm rate for that
reason. Held-out split, same baselines: 15 items, random expected recall 0.061, hunk-all F1 0.080.

## Residual weaknesses found while doing this

- A "subtract the known noise" strategy: anyone holding the dev patches of an app can flag only the
  hunks that are not in its public noise pool. To keep that out of the test split, the four apps
  that carry held-out items (sessions, vault, jobq, pager) have no public items and their noise
  pools are private. Style of the noise is still shared across apps.
- The noise hunks are visibly cosmetic. A reviewer that learns "behaviour-changing hunk" gets
  most of the localisation for free; this measures review attention, not depth of reasoning.
- Public READMEs and unit tests of the four held-out apps state the rules their defects break.
  This leaks which property is at stake, not where the defect is.
