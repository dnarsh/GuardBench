# GuardBench pre-registration (v1)

Status: written before any reviewer was run on any GuardBench defect.
Tag: `prereg-v1`. Anything changed after the tag is listed in the deviations log below.

## Claim

Current AI code reviewers miss planted security-guard defects at a measurable
rate, and that rate differs from the rate for plain logic defects.

## Design

- A defect is a unified diff that introduces one flaw into a small Python app.
- Each defect has: a test that passes on the clean app and fails on the buggy app
  (proof the defect is real), a ground-truth location (file + line range in the
  patched file), and a clean twin (a same-shaped diff to the same region that does
  not introduce the flaw), used to measure false alarms.
- Classes. Guard group: `fail-open`, `removed-validation`, `secret-leakage`.
  Logic group: `race-condition`, `off-by-one`. The grouping is fixed here, before
  results exist. Race conditions are arguably a security issue too; they are put in
  the logic group because the seeded races are check-then-act bugs with no
  attacker-facing guard, and this choice is listed as a threat to validity.
- Reviewer = any callable `diff text -> list of {file, line, text}`. No judge model.
- Hit: a comment is a hit when its file equals the defect file and its line is
  within `[start - 3, end + 3]`. A defect is found when at least one comment is a hit.
- Metrics: recall per class and per group (found / defects); clean-twin alarm rate
  (clean twins with at least one comment / clean twins); precision (hit comments /
  all comments over buggy and clean diffs; undefined when no comments); F1 =
  harmonic mean of precision and overall recall (0 when precision is undefined).
  All proportions get Wilson 95% intervals (z = 1.96).
- Split: 40% dev (public, in this repo), 60% test. The test defects are NOT committed
  to the public repo. The harness reads them from the directory in env var
  `GUARDBENCH_TEST_DIR` (layout: `apps/` and `defects/`).
- Baselines: `flag-every-hunk` (one comment per hunk at its first changed line) and
  `random` (one comment at a uniformly random new-side line shown in the diff,
  seeded per diff).

## Hypotheses

Each is evaluated per reviewer on the test split only. Dev data is for harness
debugging and may be used freely.

- H1 (misses exist). Overall recall of the reviewer is below 0.75.
  Supported if the Wilson 95% upper bound is below 0.75; refuted if the lower
  bound is at or above 0.75; otherwise inconclusive.
- H2 (the benchmark discriminates). The reviewer's F1 is higher than the F1 of both
  baselines. Supported if so on the point estimate and the reviewer's clean-twin
  alarm-rate interval lies entirely below the flag-every-hunk interval (which is
  expected to be about 1.0). If a baseline matches the reviewer, the benchmark
  cannot separate reviewers from trivial strategies and that is reported as a result.
- H3 (guard differs from logic). Recall on the guard group differs from recall on the
  logic group. Supported if the 95% interval of the difference (Newcombe hybrid
  score interval built from the two Wilson intervals) excludes zero. Two-sided; no
  direction is assumed.

No multiplicity correction: three hypotheses, reported per reviewer, all outcomes
published including null and inconclusive ones.

## Sample-size arithmetic

Worst case is p = 0.5. For a Wald-style half-width d, n = z^2 p(1-p) / d^2.

- d = 0.10: n = 3.8416 * 0.25 / 0.01 = 96.04, so n of about 96 (97 to be safe).
- d = 0.07: n = 3.8416 * 0.25 / 0.0049 = 196.0, so n of about 196.

Wilson half-width at p = 0.5 (exact, computed with the harness `wilson`):

| n | interval | half-width |
|---|----------|-----------|
| 30 | 0.3315 to 0.6685 | 0.169 |
| 60 | 0.3773 to 0.6227 | 0.123 |
| 90 | 0.3988 to 0.6012 | 0.101 |
| 96 | 0.4019 to 0.5981 | 0.098 |
| 150 | 0.4210 to 0.5790 | 0.079 |
| 196 | 0.4307 to 0.5693 | 0.069 |

Realistic target: 150 test defects (30 per class; guard group 90, logic group 60).
That gives overall precision of about +-0.08 and per-class precision of about +-0.17.
For H3 with 90 vs 60 defects, the 95% half-width of the difference at p = 0.5 is
1.96 * sqrt(0.25/90 + 0.25/60) = 0.163, and the smallest difference detectable with
about 80% power is 2.8 * sqrt(0.25/90 + 0.25/60) = 0.233. Smaller guard-vs-logic
gaps will come out inconclusive; that is accepted and will be reported as such.

With 150 test defects (60%) the dev split (40%) would be 100 defects. The foundation
milestone ships only 10 dev pairs; growth is a later milestone.

## Kill criteria

The study is stopped, or reported only as a pilot, if any of these happens:

1. Fewer than 100 validated test defects exist when reviewers are first run
   (report as a pilot, no H1-H3 verdicts).
2. More than 10% of authored test defects fail `validate` (the defect generator is
   unreliable; fix it before running any reviewer).
3. The `random` baseline finds more than 70% of defects (localisation is too easy
   to be informative; redesign locations, e.g. larger diffs, before running).
4. Any validated test defect is found to be leaked into a reviewer's public
   training or prompt material (drop it and log it).
5. A bug in the scorer is found after reviewers ran: fix, re-score all outputs, log it.

## Threats to validity

- Synthetic bugs: seeded defects are not field bugs; they may be easier or harder.
- Small n: intervals are wide; per-class claims are weak.
- Tiny diffs: with diff-sized context, localisation is easy, so recall mostly
  measures "commented at all". This is why the clean-twin alarm rate, precision and
  the flag-every-hunk baseline are part of the design.
- Contamination: the dev split and the apps are public and can enter training data.
  The test split stays private until after reviewers ran.
- Author bias: one author wrote defects and tests; clean twins may be recognisable
  by style. Not controlled in v1.
- Class grouping is a judgement call (see Classes).
- Location tolerance of +-3 lines is a choice; sensitivity at 0 and 5 is reported.
- Reviewer nondeterminism: single runs per reviewer unless stated; repeats, if any,
  are reported separately.
- Python only, small apps; results do not generalise to other languages or to
  repo-scale review.

## split.sha256 rules

- `prereg/split.sha256` holds the tree hash of the private test split. It is
  `PENDING` in the `prereg-v1` tag.
- Hash algorithm (`python -m guardbench hash DIR`): sha256 over lines
  `<posix relative path>\0<sha256 of file bytes>\n`, files sorted by path.
- Before any reviewer is run on the test split, the hash is computed over the final
  test directory and committed to `prereg/split.sha256` in its own commit, which gets
  the tag `prereg-v1-split`. After that the test directory must not change; if it
  does, the new hash is committed, logged below, and earlier runs are void.

## Deviations log

(none yet; entries are `date, what changed, why, effect on analysis`)
