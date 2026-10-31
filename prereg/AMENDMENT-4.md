# Amendment set 4: prospective reporting eligibility and uncertainty limits

2026-11-01. This is a new amendment set, not a replacement for amendment **A4** (the harness/naming
entry in amendment set 2). `PREREGISTRATION.md`, `AMENDMENTS.md`, the tagged `prereg-v1`/`v2`/`v3`
artifacts, `split.sha256` and the apps remain unchanged. No private held-out items are edited by this
amendment. The existing baseline/toy results in `docs/RESULTS.md` remain historical descriptive data.

## A10. A prospective reporting minimum, not a rewrite of the v1 kill criterion

The literal v1 kill criterion 1 was **fewer than 100 validated test defects when reviewers are first
run**. Its sample-size target was 150. These are distinct statements: reaching 100 stopped tripping
that literal size criterion, but did not itself establish that the 150 target had been reached.
Amendment set 3 A8 already classified every run on the 100-item cohort as a pilot.

From this amendment forward, H1/H3 verdicts in `guardbench hyp` require a prospectively registered,
confirmatory held-out cohort of **at least 150 validated items**, with exact frozen manifest/apps
hashes and count. This is a stricter prospective reporting gate, not a claim that v1 always had a
150-item kill threshold. Other kill criteria and validity requirements remain in force; passing the
software eligibility check is not evidence that every scientific requirement has been satisfied.

The current `prereg-v3` registry entry is explicitly pilot-only:

- 100 held-out items.
- Manifest `ae29a20ee5b1f9e2a86d714805f5e20776148f268ef9e45375ef70b7c5927990`.
- Apps hash `8b3fd772266b3ec05f073db8a3632d10ae99507c2879b304d7fb7a3b4f97cc1d`.

No purpose/role flag, altered count or caller-provided `eligible`, `minimum` or mode value promotes
this cohort to confirmatory status. A future cohort requires a new prospective amendment and a
committed registry entry before confirmatory analysis. Unit tests may use explicitly synthetic
registry fixtures; those fixtures are not registered study cohorts or benchmark observations.

## A11. Run context and descriptive fallback

Run JSON records a versioned `analysis` block: purpose (`pilot` by default), effective split,
protocol, dataset manifest/apps hashes, and reviewer label, declared role and transport.
Eligibility requires an explicit confirmatory purpose, held-out split, registered confirmatory
cohort and exact registry/count match, plus a declared model/human reviewer using a command or
Python callable. A command is only a transport; it is not evidence of a model. Built-in baselines
retain the baseline role. `--root` overrides `--split` and records custom input as `custom`.

Legacy/missing or incompatible metadata and all ineligible runs retain descriptive recall and
H3 difference estimates, but return `analysis_status: not_evaluated`, eligibility reasons and no
H1/H3 verdicts. Rates/intervals are recomputed from validated counts. H2 is not implemented by this
command; it must not be inferred from an H1/H3 output. The mathematical `h1_verdict` helper remains
available for numerical checks, and calling it directly is not an eligible study report.

This metadata is advisory provenance. It does not authenticate a reviewer identity or bind edited
JSON to raw reviewer responses. Exact hashes/counts are necessary context checks, not proof of
dataset independence, successful item validation, an untripped authoring-failure criterion, or no
contamination. Raw outputs, source revisions and validation receipts still have to be retained.

The generated `report` command contains only baseline/toy rows and is always descriptive, even if
given 150 or more items. Its size note reflects the count supplied to that run and does not claim
that every possible held-out cohort is below target. Numerical baseline differences are not
hypothesis verdicts.

## A12. Precision/F1 uncertainty is not supplied

V1's wording that all proportions receive Wilson intervals was broader than the implemented
report. Recall and clean-twin alarm rates receive Wilson 95% intervals. Recall differences receive
Newcombe hybrid-score 95% intervals as specified. **Comment precision and F1 remain descriptive
point estimates only**, with no uncertainty interval claimed by the current harness.

F1 is a harmonic function of precision and recall, not a binomial proportion; attaching a Wilson
interval directly to F1 would not implement the promised uncertainty. Comment-level observations
and items sharing an app can also be dependent. This amendment narrows the reporting claim rather
than inventing an uncertainty method after seeing results. The printed Wilson/Newcombe intervals
do not adjust for app clustering. Any future precision/F1 uncertainty analysis needs its own
prospectively specified resampling/modeling unit and assumptions. H2's historical point-estimate
and alarm-rate comparison rule is preserved; no new H2 conclusion is introduced here.

## A13. Correct the wording of the legacy pre-freeze chronology

Amendment set 2's header says that running the two baselines on its 15 held-out items before the
split hash was committed was allowed by v1. The literal v1 rule instead said **before any reviewer
is run**, and its own reviewer definition was any callable producing comments. These baselines
therefore constitute a disclosed exception/deviation to that literal chronology; describing them
as automatically allowed was too broad. This amendment corrects the interpretation without
rewriting the frozen document or erasing the runs.

The 85 new held-out items have a separately documented sequence in amendment set 3 A7: construction
and validation, private commit/fresh-clone manifest verification, amendment/hash freeze, then the
baseline/toy runs. That chronology is preserved as documented and is not collapsed into the earlier
15-item exception. This amendment does not claim a new independent validation of either history or
turn baseline/toy outputs into evidence about a model. All current results remain descriptive.
