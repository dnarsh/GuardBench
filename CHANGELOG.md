# Changelog

## v0.2.0 (milestone 3)

- 8 new apps (`tickets`, `invites`, `shipping`, `links`, `leases`, `feeds`, `quota`, `pkgindex`): 20 apps.
  New directories only; the original 12 apps are unchanged (hash `a83db71f...`, amendment A6).
- Dev split 20 to 30 pairs (6 per class); held-out split 15 to 100 pairs (20 per class), private repo.
  New manifest hash in `prereg/split.sha256`; amendment set 3, tag `prereg-v3`.
- `guardbench report` writes `docs/RESULTS.md` (baselines, toy reviewer, Wilson and Newcombe intervals,
  no-verdict banner). `guardbench hash DIR --only NAME ...`.
- `command` reviewer streams stdout with a hard 1 MiB cap, bounds stderr, and fails instead of hanging
  when a leftover process holds the pipe (closes the milestone-2 open finding).
- `examples/toy_reviewer.py`, a labelled toy baseline, with tests. `tools/gen_noise.py`.
- Written review: `docs/reviews/command-reviewer-and-example.md`.
- Still no model run, no verdict for H1 to H3.

## v0.1.0 (milestone 2, tag `prereg-v2`)

- 12 apps, 35 pairs (20 dev, 15 held out), multi-hunk items, validator hardening, reviewer adapter,
  `hyp`, manifest hash, amendments 1 to 5.
