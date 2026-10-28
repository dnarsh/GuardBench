# Differential review: validator and sandboxing (milestone 2)

Method: the `differential-review` skill, applied by the author agent to its own change. This is a
self-review, not an independent one; see "Coverage and confidence".

- Baseline: `de80d6c` (milestone 1). Reviewed commits: `b03685a` (validate hardening),
  `89dcd2d` (reviewer adapter, manifest, heldout env var), `4dcf80d` plus the `write_items` fix
  made during this review (item builder).
- Codebase size: SMALL (about 12 modules), so a DEEP read of every changed function was done.
- Risk classification: HIGH for `guardbench/validate.py` (executes untrusted code, process control)
  and `guardbench/reviewers.py` (spawns user commands); MEDIUM for `guardbench/build.py` (writes
  files from specs); LOW for scoring/statistics additions.
- Git context: the removed code was the `subprocess.run(..., timeout=)` call. Its history is the
  single milestone-1 commit; it was the cause of the bug being fixed (a timeout killed only the
  direct child, and `communicate()` then hung while a grandchild held the pipe). No removed
  security checks: every previous control (scrubbed env, `-E -s -B`, copy in a temp dir, no
  stdin, patch confinement) is still present.

## Blast radius

`run_tests` has 1 production caller (`validate_defect`, which is called 3 times per defect by the
CLI and by every dataset test) and 2 test callers. `kill_tree` has 2 callers (`run_tests`,
`command_reviewer`). Quantitatively small, but every defect validation and every CI run goes
through it.

## Test coverage of the changed code

`tests/test_sandbox.py` covers: grandchild killed on timeout (proved by a heartbeat file that stops
growing; the same test hung before the fix), environment scrub and temp HOME, outgoing connection
refused (the listening server never sees a connection), output cap, normal pass/fail.
`tests/test_reviewers.py` covers the command adapter (schema, exit code, bad JSON, timeout,
missing program). Not covered: the POSIX branch of `kill_tree` (CI on Linux exercises it, my local
run was Windows), a process that leaves its process group, and an output flood from a grandchild.

## Findings

| # | Severity | Location | Finding | Status |
|---|----------|----------|---------|--------|
| 1 | Medium | `validate.py:104` `kill_tree` after `p.wait()` | On POSIX the group is signalled after the leader was reaped. The pgid stays valid while any member lives, which is the case we want, but if no member lives and the pid was recycled to another group leader, an unrelated group could be killed. Needs a pid reuse inside microseconds. | Accepted and documented. A `waitid(WNOWAIT)` ordering would remove it. |
| 2 | Medium | `validate.py:35` `BOOT` | The network block is a Python-level monkey-patch. `ctypes`, `_socket`, `subprocess` (curl) and DNS via other libraries bypass it. A malicious test module can reach the network. | Accepted; stated in the module docstring and README. Real isolation needs a container/VM. |
| 3 | Medium | `validate.py:58` Windows `taskkill /T` | `/T` follows parent links; a grandchild whose parent already exited is no longer in the tree and survives. A test can start a detached process. | Accepted; documented. A Windows job object would close it. |
| 4 | Low | `validate.py` | No CPU, memory or disk quota. A test can fill the temp HOME or exhaust RAM within the timeout. Output size is capped, disk is not. | Accepted; documented. |
| 5 | Low | `reviewers.py:51-59` | `communicate()` buffers all reviewer stdout before the `MAX_STDOUT` check, so a hostile or buggy reviewer command can use unbounded memory for the timeout duration. Reviewer commands are user supplied and are intentionally not sandboxed (they need keys and network). | Open. Acceptable for a trusted local command; fix by streaming with a cap before any untrusted reviewer is run. |
| 6 | Low (fixed) | `build.py` `write_items` | A spec `id` such as `../x` was joined into the output path (spec files are trusted authoring input, but the held-out specs come from a second repo). | Fixed here with the same name rule as the loader, plus a test written first (it failed, then passed). |
| 7 | Info | `build.py` `_text` | Edit file names are restricted to top-level, non-test, non-dot names, so noise or spec edits cannot touch the test module or other paths. | Verified. |
| 8 | Info | `cli.py` `_load` | The held-out split reads only `defects/` from `$GUARDBENCH_HELDOUT`; apps always come from the public `apps/`, so a held-out directory cannot substitute app code. A manifest mismatch is not enforced at run time. | Open: `run` does not recompute and compare `prereg/split.sha256`. Done by hand and recorded in the amendment. |

## Adversarial check (HIGH risk files)

Attacker: someone who submits a defect item or a held-out directory.
- Escape the app copy by a patch: blocked by `patch.apply` (unchanged, strict paths, realpath check).
- Edit the test module to make a bug "fail": blocked by the existing rule and unchanged.
- Read the host environment for secrets: the child sees only TMP/HOME/SYSTEMROOT. It can still read
  files and registry as the user (finding 2/4).
- Hang the harness: timeout plus tree kill plus the 5 s reader join; a pipe held by an escaped
  grandchild cannot block the harness beyond that join.
- Flood output: killed at 4 MiB (tested).

## Coverage and confidence

All changed functions in the three modules were read in full. The POSIX kill path was not run
locally; it is exercised by GitHub Actions (Ubuntu). Confidence: medium-high that the controls do
what they claim, high that they are not a security boundary. Findings 1 to 5 are known limits, not
regressions.
