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

---

# Amendment set 3 (milestone 3, tag `prereg-v3`)

Written before any baseline or reviewer was run on the new held-out items. Amendments 1 to 5 above
are not edited. No model call and no API key exists anywhere in this repository; nothing here is a
result about any model.

## A6. What changed and the apps rule

- Eight apps were added in new directories only: `tickets`, `invites`, `shipping`, `links`, `leases`,
  `feeds`, `quota`, `pkgindex` (apps 13 to 20; 20 apps now ship).
- Amendment A3 said that changing any file under `apps/` voids the held-out items. **No file of the
  original 12 apps was changed**, so the 15 milestone-2 held-out items stay valid. This is checked,
  not asserted: `python -m guardbench hash apps --only <the 12 names>` still gives
  `a83db71f746a6ca69313496c5119bc5099571f3503cca195069d1af1f3468704`, the value recorded in A3, and
  `tests/test_dataset.py::test_the_original_twelve_apps_are_byte_for_byte_the_prereg_v2_apps` fails
  if it ever changes.
- The eight new apps are hashed separately (`--only` those eight names):
  `4771b63b21019fd233ffeda7af164dc4fa81e9233cf6a92cfdbb13662cc48193`. The hash of the whole `apps/`
  tree at this amendment is `8b3fd772266b3ec05f073db8a3632d10ae99507c2879b304d7fb7a3b4f97cc1d`.
  From now on a change to a new app voids exactly the held-out items built on it, and a change to one
  of the original 12 voids the items built on it; either must be recorded as a further amendment.
- The new apps are small (about 150 lines of logic in 5 modules plus a test module and README), each
  with 10 or 15 independent guard sites, each covered by one test.

## A7. Split sizes, balance and the hash

| | apps with items | pairs | per class |
|---|---|---|---|
| public dev | 9 (8 original, `tickets`) | 30 | 6 |
| held out (private repo) | 11 (`sessions`, `vault`, `jobq`, `pager`, `invites`, `shipping`, `links`, `leases`, `feeds`, `quota`, `pkgindex`) | 100 | 20 |

- The 15 milestone-2 held-out items are unchanged; their own manifest (recomputed from the private
  repo's files) is still `3343e5b85c3524f4a9d7e6d8e8bea1cfe7a3b3e232362114d5db03aba923383a`.
- The 85 new held-out items are all on the seven new held-out apps (15 each on `invites`, `shipping`,
  `links`; 10 each on `leases`, `feeds`, `quota`, `pkgindex`). The 10 new dev items are all on `tickets`.
  The split stays by app, so no app has items in both splits.
- Every item was built by `guardbench build` (8 to 25 hunks over 3 to 6 files, one defect hunk among
  benign noise) and passed `guardbench validate` (clean app passes, bug fails, clean twin passes,
  location overlaps the defect hunk). The held-out items were validated through `GUARDBENCH_HELDOUT`.
- The new manifest hash of the 100 held-out items is recorded in `prereg/split.sha256`:
  `ae29a20ee5b1f9e2a86d714805f5e20776148f268ef9e45375ef70b7c5927990`. It was reproduced from a fresh
  clone of the private repo at its commit `3d06fa8` (the repo pins `eol=lf`).

**Order of operations, honestly**: (1) wrote the apps and their tests; (2) built and validated the
items (validation executes the apps' tests, no reviewer; the builder also checks hunk and file counts);
(3) committed and pushed the private items, recomputed the manifest from a fresh clone; (4) wrote
this amendment and `split.sha256` (this commit, then tag `prereg-v3`); (5) only after that were the
two baselines (`random`, `hunk-all`) and the toy example reviewer run on the new held-out items, and
only to produce `docs/RESULTS.md`. No baseline had touched the new held-out items before step 4. The
pre-registered baselines had already been run on the 15 milestone-2 held-out items (see the header
of this file).

## A8. Kill criterion 1 and the pilot rule

The held-out split now has 100 validated defects, so the literal "fewer than 100" test of kill
criterion 1 is no longer tripped. The pre-registered **target** is 150 held-out defects, and 100 is
below it, so **every run on this split is reported as a pilot**. In addition, no hypothesis (H1 to H3)
has a verdict without real reviewer runs, and none exists. `docs/RESULTS.md` prints both statements.

## A9. Deviations and new limits

- The new apps are smaller and more uniform than the milestone-2 ones, because 100 independent sites
  were needed. They were written by one AI agent in one session; the guard sites share a style
  (a guard in a function with an obvious name, a unit test next to it). The rule each defect breaks is
  named in the app's public README and tests, as in milestone 2.
- Noise of the new apps is generated by the public `tools/gen_noise.py` (one-line docstrings and an
  extended module docstring). It is behaviour-preserving and checked, but it is cosmetic and
  **reproducible by anyone from the public apps**: the milestone-2 argument that private noise pools
  stop a reviewer from subtracting benign hunks holds only weakly for the new held-out items (the
  builder's choice of which groups appear stays private). Docstring-only hunks are an obvious
  artifact a reviewer could learn to ignore.
- Defects are synthetic, one-line to a-few-line edits planted by the author; they carry planted-bug
  style artifacts (for example a flipped return value in an `except` branch, a dropped `raise`).
- Class balance is exact (20 held out and 6 dev per class), apps are not balanced across classes.
- Hunks are 8 to 14 in the new items; the 25-hunk end of the range is unused.
- A `command` reviewer buffered all output before checking its 1 MiB cap (an open finding from the
  milestone-2 review). It now streams with a hard cap; see `docs/reviews/`.
