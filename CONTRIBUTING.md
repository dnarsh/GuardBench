# Adding a defect

An item is a seeded defect composed with benign noise. You write two small things; the builder
does the rest.

1. An app in `apps/<app>/`: 4 to 6 flat Python modules, a `README.md`, and exactly one `unittest`
   module (`test_<app>.py`), standard library only. It must pass its own tests.
2. A noise pool `noise/<app>.json`: a list of groups, each a list of `{"file", "old", "new"}` edits
   that are behaviour-preserving (docs, comments, renames, equivalent refactors). A group holds all
   sites of one change. At least 15 groups; `old` must occur exactly once in the file; edits cannot
   touch the test module. `tests/test_noise.py` applies the whole pool and runs the app tests.
3. A spec `specs/<id>.json`:

```json
{"id": "app-fail-open", "app": "app", "class": "fail-open", "file": "policy.py",
 "bug":   [{"file": "policy.py", "old": "return False\n", "new": "return True\n"}],
 "clean": [{"file": "policy.py", "old": "...", "new": "..."}]}
```

   `class` is one of `fail-open`, `removed-validation`, `secret-leakage`, `race-condition`,
   `off-by-one`. The `clean` edit is a same-shaped change that does not plant the flaw.

Build and check:

```
python -m guardbench build specs/app-fail-open.json --out build
cp -r build/defects/app-fail-open defects/
python -m guardbench validate
python -m guardbench baselines
```

`build` picks a deterministic noise subset (seeded by the id) and fails unless the diff has 8 to 25
hunks over 3 to 6 files. `validate` enforces that the app's test passes on the clean app and the
clean twin, fails on the bug, and that the recorded location overlaps the defect hunk.

Rules:

- Exactly one defect hunk; noise stays at least 8 lines away (the builder guarantees it).
- Race defects must be deterministic: a hook plus a timed barrier, never `sleep` and hope.
- No code copied from existing projects; no secrets, emails or personal data.
- Do not edit `apps/` after a split hash is recorded: it voids the held-out items.

Test-split defects are never committed to this repository. They are built from their own specs and
noise pools in the private repo and read through `GUARDBENCH_HELDOUT`. Run `python -m pytest -q`
before opening a pull request.
