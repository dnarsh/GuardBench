# Reviewer adapters

```
python -m guardbench run --reviewer hunk-all
python -m guardbench run --reviewer random --seed 3
python -m guardbench run --reviewer command --command python my_reviewer.py
python -m guardbench run --reviewer mypkg.mod:review      # a Python callable instead
python -m guardbench run --split test ...                 # needs GUARDBENCH_HELDOUT
python -m guardbench run --reviewer random --json > run.json && python -m guardbench hyp run.json
```

`--command` takes the rest of the line (it must be the last option); the program is started once
per diff, without a shell. A `--reviewer-timeout` (default 120 s) kills it and its children.

## Declared analysis context

`run --json` records an `analysis` metadata block with `schema_version: 1`, the effective split,
purpose, protocol, dataset manifest/apps hashes and reviewer label/role/transport. The CLI flags are:

- `--analysis-purpose pilot|confirmatory` (default `pilot`).
- `--reviewer-role unknown|model|human` (default `unknown`).
- `--protocol NAME` (default `prereg-v3`).

Put these options before `--command`, which consumes the remaining arguments. For example, this
records an explicitly declared model reviewer while retaining the default pilot purpose:

```
python -m guardbench run --split test --reviewer command --reviewer-role model --json --command python my_reviewer.py
```

This example requires the user's private held-out checkout and their own reviewer implementation;
it is not a model integration supplied by GuardBench. Running an external program is not evidence
that it used a model. Labels and roles are declarations, not authenticated identities. Built-in
`random` and `hunk-all`/`flag-every-hunk` remain `baseline` regardless of a role flag. The report's
labelled toy script is also descriptive.

`--root` takes precedence over `--split`, and is always recorded as `custom`; writing `--split test`
beside it cannot turn custom data into an eligible held-out cohort. Command/callable transport,
an explicit model/human declaration and `--analysis-purpose confirmatory` are necessary context for
eligible reporting, but are not sufficient. The committed protocol registry must separately mark
the cohort confirmatory and bind its exact manifest, apps hash and count, with at least 150 items.
The current `prereg-v3` cohort has 100 items and remains pilot-only. A future eligible cohort requires
a prospective protocol amendment and registry entry, not a JSON-supplied minimum or eligibility bit.

`guardbench hyp run.json` validates the counts and recomputes recall/intervals. Ineligible or legacy
metadata yields `analysis_status: not_evaluated`, reasons and descriptive H1/H3 estimates without
verdicts. This command does not implement H2. Precision and F1 remain descriptive point estimates;
Wilson intervals apply to recall and clean-twin alarm rates, and Newcombe intervals to reported
differences. See [amendment set 4](../prereg/AMENDMENT-4.md).

These checks are an analysis-reporting guard, not a signature or independent verification of raw
reviewer output, cohort validity or the role claim. Do not edit metadata to manufacture provenance.

## Contract of `command`

stdin: one unified diff, UTF-8 (the same `--- a/PATH` / `+++ b/PATH` text the patches contain).

stdout: JSON, either a list or an object with a `findings` list:

```json
[{"file": "policy.py", "line": 20, "text": "returns True on unknown user"}]
```

- `file`: string, path as in the diff without `a/` or `b/`.
- `line`: integer >= 1, a line number in the new (patched) file. Booleans are rejected.
- `text`: optional string, free text, not scored.
- An empty list means "no findings".

A non-zero exit, a timeout, invalid JSON, stdout over 1 MiB (the process is killed as soon as the
cap is crossed, not after it finishes), a process left holding the output pipe after the timeout, or a finding that breaks the schema is a
reviewer error: the run stops with `reviewer error: ...` and exit code 1. It is never silently
scored as "no findings".

The command runs with your environment (so it can use your own keys) and is not sandboxed. The
harness itself makes no network calls and holds no keys. Scoring is described in the README.

## Example

[`examples/toy_reviewer.py`](../examples/toy_reviewer.py) is a complete reference implementation of this
contract. It is a **toy baseline** (it flags blocks that remove more guard-looking lines than they add)
and its numbers are in [`RESULTS.md`](RESULTS.md); it is not a tool to use on real code.
