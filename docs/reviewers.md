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

A non-zero exit, a timeout, invalid JSON, stdout over 1 MiB or a finding that breaks the schema is a
reviewer error: the run stops with `reviewer error: ...` and exit code 1. It is never silently
scored as "no findings".

The command runs with your environment (so it can use your own keys) and is not sandboxed. The
harness itself makes no network calls and holds no keys. Scoring is described in the README.
