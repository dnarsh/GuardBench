# Pre-registration amendments

`PREREGISTRATION.md` (tag `prereg-v1`) is not edited. Changes live here. This file is amendment
set 2, tag `prereg-v2`, written before any external reviewer was run on any item. The only things
run on the test split so far are the two pre-registered baselines (structure counts for the kill
criterion 3 check) and `validate`; both were run before the split hash was committed, which the
v1 rules ("before any reviewer is run") allow, and are listed here for transparency.

## A1. Kill criterion 3 was tripped on dev, and what changed

On the 10 milestone-1 pairs the `random` baseline found 10/10 (Wilson 95% [0.722, 1.000]); the
limit was 70%. The design was changed, as the criterion requires ("redesign locations, e.g.
larger diffs"), before any reviewer was run: every item is now a multi-hunk, multi-file diff
(8 to 25 hunks, 3 to 6 files) in which the defect is one hunk among validated benign noise hunks.
Details and numbers: `docs/noise-iteration.md`. After the change, exact expected `random` recall
is 0.062 on dev (0.061 on the held-out split), versus 0.70 limit. Criterion 3 stands unchanged.
The "Tiny diffs" threat to validity is reduced, not removed (see the doc).

## A2. Dataset size, split and kill criterion 1

- 12 apps, 35 validated pairs: 7 per class (fail-open, removed-validation, secret-leakage,
  race-condition, off-by-one). 20 pairs are public dev, 15 are held out (3 per class).
- Dev share is 57%, not the planned 40%, because the 10 milestone-1 pairs were already public.
  The 25 new pairs were split 10 dev / 15 test.
- The split is by app, not by item, so the benign noise of a held-out app is never visible next to
  public items: held-out apps are `sessions`, `vault`, `jobq`, `pager` (no public items, private
  noise pools); dev apps are the other eight. The four held-out apps were chosen so that each
  class has exactly 3 test items. Their source, README and unit tests are public.
- **Kill criterion 1 applies**: fewer than 100 validated test defects exist (there are 15), so any
  reviewer run on this split is reported as a pilot with no H1 to H3 verdicts. The scripts exist
  (`guardbench hyp`); the verdict strings they print are not to be reported until criterion 1 is
  met. The sample-size arithmetic in v1 is unchanged and the 150-defect target stands.

## A3. Split hash definition

v1 defined the hash as the tree hash of the test directory. Replaced by a manifest hash
(`python -m guardbench manifest DIR`): for each `DIR/defects/<id>/`, item hash = sha256 over sorted
`<relative path>\0<sha256 of bytes>\n` lines of the item directory (`defect.json`, `bug.patch`,
`clean.patch`); manifest = sha256 over the sorted item hashes, each followed by `\n`. The value in
`prereg/split.sha256` is that manifest for the 15 held-out items. A fresh clone of the private repo
reproduces it (the private repo pins `eol=lf`).

Because the manifest covers items only, the apps the items apply to are fixed separately:
`python -m guardbench hash apps` at tag `prereg-v2` is
`a83db71f746a6ca69313496c5119bc5099571f3503cca195069d1af1f3468704`. Changing any app file after this
tag voids the held-out items.

## A4. Harness and naming changes

- Env var `GUARDBENCH_TEST_DIR` is replaced by `GUARDBENCH_HELDOUT`. Layout: only `defects/` is
  read from it; apps always come from the public `apps/`.
- `score` is now `run` (`score` kept as an alias); `flag-every-hunk` is also called `hunk-all`.
- `validate` was hardened (process-tree kill, scrubbed env with temp HOME, no outgoing sockets,
  capped output). It is still not a sandbox; limits are in the module docstring and the written
  review `docs/reviews/validator-and-sandbox.md`.
- Reviewer adapter added (`run --reviewer hunk-all|random|command`); H1 and H3 interval script
  added (`guardbench hyp`, Newcombe hybrid score as specified in v1).

## A5. Deviations, honestly

- The dev:test ratio and the test size (A2) differ from v1's plan.
- Hunk counts are 8 to 13 in dev and 9 to 15 in test, mean about 11; the allowed range is 8 to 25.
  The upper range is unused; more noise would lower `random` further.
- `hunk-all` keeps recall 1.0 by construction; only its precision, F1 and alarm rate are far from
  the ceiling. v1 H2 already compares F1 and alarm rates.
- One author (an AI agent) wrote apps, defects, noise and tests; noise is visibly cosmetic and
  shared in style across apps. The test split is not independent of dev in style.
- The held-out apps' public READMEs and tests name the rule each defect breaks.
- Noise hunks are mostly comments, docstrings and small refactors. Test-module edits as noise are
  impossible by rule, so "tests" noise from the brief is absent.
- Validation was run on Windows (Python 3.12 runtime); CI runs Linux on 3.10 and 3.12.
