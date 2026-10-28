# Differential review: streaming command reviewer, toy example, noise generator (milestone 3)

Reviewer: the author agent (Claude Sonnet 5.5). **This is a self-review**, not an independent audit.
Method: the differential-review workflow (triage, history, blast radius, tests, adversarial pass),
scaled to a small codebase (about 1,500 lines of harness plus 8 small apps), so a deep read.

## Scope and risk triage

| Change | Touches | Risk |
|---|---|---|
| `guardbench/reviewers.py` `command_reviewer`: stream stdout with a hard cap, bound stderr, feeder/reader threads | subprocess, untrusted output of user-supplied commands | HIGH |
| `examples/toy_reviewer.py` | parses an untrusted diff from stdin | MEDIUM (read-only, no I/O besides stdin/stdout) |
| `tools/gen_noise.py` | reads app source, writes JSON | LOW |
| `guardbench/defects.py` `tree_hash(only=)`, `cli hash --only` | file reads under a directory | LOW |
| `guardbench/report.py` | runs the toy script through `command_reviewer`, reads held-out items | MEDIUM |
| 8 new apps | only executed by `validate` and the tests, under the existing validator | see "Apps" |

## Baseline (history)

`git log -p guardbench/reviewers.py`: the milestone-2 `command_reviewer` called `communicate()` and
checked `len(out) > MAX_STDOUT` after the process ended. The milestone-2 review listed this as an
open finding: a reviewer that prints without end is held in memory until the timeout (up to
`--reviewer-timeout`, default 120 s); stderr was unbounded too.

## Findings

1. **FIXED (was open): unbounded buffering of stdout and stderr.** stdout is now read in 64 KiB
   chunks and the process tree is killed the moment more than 1 MiB has arrived; stderr keeps only
   its last 4000 bytes. Tests: `test_output_cap_is_enforced_while_streaming_not_after_buffering`
   (an endless writer is cut off in under 10 s although its timeout is 20 s; it failed on the old
   code with "timed out"), `test_stderr_flood_is_bounded_and_the_tail_is_reported`.
2. **FOUND AND FIXED during this review: the first streaming version did not honour the timeout
   when a grandchild kept the pipes open.** If the reviewer exits but a child it started still holds
   stdout, the reader threads block until that child ends, and closing the pipe blocks too (observed:
   25 s with a 10 s timeout, 30 s in the regression test). Now the readers are joined only until the
   original deadline, the pipes are not closed while a reader is alive, and the run fails with
   "reviewer left a process holding its output open". Test:
   `test_a_leftover_child_holding_stdout_cannot_outlive_the_timeout`. On POSIX the process-group kill
   reaps the grandchild (the CI run on Linux showed the run then simply succeeds), so the test accepts
   either outcome and asserts only that the run is shorter than the grandchild's sleep.
3. **OPEN, documented: a leftover process is not killed.** On Windows `taskkill /T` only follows
   children of a live parent, and a POSIX child that calls `setsid` leaves the group. The leftover
   keeps running after the error is raised. Mitigation is outside this harness (run reviewers in a
   container). Already stated in the README security model.
4. **OPEN, by design: the `command` reviewer is user code, runs with your environment and is not
   sandboxed.** Unchanged.
5. **Toy reviewer: no finding.** It reads stdin only, uses no `eval`, `open`, `subprocess`, socket or
   environment access, and its regex is linear (no nested quantifiers). Probed with a hunk header
   claiming 99,999,999,999 lines followed by 200,000 removed lines: 0.13 s, bounded by the actual
   number of input lines, because the loop advances through real lines only. Junk and binary input
   gives `[]` and exit 0 (tested). A diff is only text here and is never applied or executed.
6. **Noise generator: no finding.** It writes only to stdout, reads `*.py` of one directory it is
   given, and the builder (`guardbench build`) still checks every group applies and the app tests
   still pass (`tests/test_noise.py` for public pools, a local check for the private ones).
7. **Hash `--only`: no finding.** Names are looked up with `os.path.exists(join(dir, name))`
   and filter `os.walk` top-level entries; a name such as `..` or an absolute path is not rejected
   but only changes what is hashed (an integrity check, not a security boundary). Unknown names raise.

## Blast radius

`command_reviewer` has 3 callers in the harness: `reviewers.get`, `report._toy`, and the tests
(`grep -rn command_reviewer`). `tree_hash` has 2 callers (`cli hash`, `item_hash`); the default
(`only=None`) path is unchanged and covered by the manifest tests.

## Apps (new, executed by `validate`)

The 8 new apps run only inside the existing validator (temp copy, scrubbed environment, network
blocked by a Python patch, tree kill, 4 MiB output cap), which is not a sandbox
(`validator-and-sandbox.md`). The apps use `threading`, `hashlib`, `hmac`, `ipaddress`, `re` and
nothing else; no file, socket or subprocess use. Race tests use barriers with a 0.3 s timeout, so a
broken lock costs time, not a hang.

## Test coverage of the changed code

Streaming cap, stderr bound, late reader of a 5 MB stdin diff, leftover child, existing schema and
exit-code tests (19 tests in `tests/test_reviewers.py`); toy reviewer (9 tests including end-to-end
through the harness); `tree_hash(only=)` and the frozen-apps hash; the generator on a temp app.
Not covered: Windows-vs-POSIX differences in process-tree kill (CI is Linux, development was on
Windows; both ran the suite).

## Coverage limits and confidence

Self-review by the code's author with no second pair of eyes. Dynamic probes were run on Windows
only; the Linux CI run is the second environment. Confidence: medium that the harness code has no
remaining unbounded-memory or hang path in `command_reviewer`; low that no process-escape path exists
(finding 3).
