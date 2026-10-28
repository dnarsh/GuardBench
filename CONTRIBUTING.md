# Adding a defect

A defect needs an app in `apps/<app>/` (3-6 Python files plus one `unittest` module, standard
library only) and a directory `defects/<id>/` with:

- `defect.json`: `id` (must equal the directory name, `[a-z0-9_-]`), `app`, `class` (one of
  `fail-open`, `removed-validation`, `secret-leakage`, `race-condition`, `off-by-one`),
  `test_module` (module name, no `.py`), `file` (path of the buggy file inside the app, `/`
  separators), `start`, `end` (1-based line range in the **patched** file).
- `bug.patch`: unified diff that plants exactly one flaw.
- `clean.patch`: same-shaped diff to the same region that does **not** plant the flaw.

Make the patches from copies of the app:

```
cp -r apps/foo /tmp/a && cp -r apps/foo /tmp/b   # edit /tmp/b
cd /tmp && diff -u a/mod.py b/mod.py   # then rename headers to "--- a/mod.py" / "+++ b/mod.py"
```

Rules, all enforced by `python -m guardbench validate`:

1. The test module passes on the clean app, **fails** on the app with `bug.patch`, and passes with
   `clean.patch`. A defect whose test does not fail is rejected.
2. Patches use `--- a/PATH` / `+++ b/PATH` headers, edit existing files only, no `..` or absolute
   paths, and must not edit the test module.
3. The `start`-`end` range overlaps the lines the patch adds (for a pure deletion, the two
   surviving lines around it).
4. Race defects must be deterministic: use a hook plus a timed barrier, never `sleep` and hope.
5. Do not copy code from existing projects, and put no secrets, emails or personal data in anything.

Test-split defects are never committed here; see the README.
Run `python -m pytest -q` before opening a pull request.
