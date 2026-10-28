"""Generate a benign-noise pool for an app: python tools/gen_noise.py apps/<app> > noise/<app>.json

Edits are behaviour-preserving by construction: add a one-line docstring to every function or class
that has none, and extend each module docstring. `tests/test_noise.py` (public pools) and
`guardbench build` re-check that every group applies and the app tests still pass.
This is cosmetic noise by design; see "Honest limits" in the README.
"""
import json
import os
import re
import sys

DEF = re.compile(r"^( *)(def|class) (\w+)\b[^\n]*:\n$")


def _words(name):
    return re.sub(r"\s+", " ", name.strip("_").replace("_", " ")).strip() or name


def pool(app_dir):
    app = os.path.basename(os.path.normpath(app_dir))
    groups = []
    for fname in sorted(os.listdir(app_dir)):
        if not fname.endswith(".py") or fname.startswith("test_"):
            continue
        with open(os.path.join(app_dir, fname), encoding="utf-8", newline="") as fh:
            lines = fh.read().splitlines(keepends=True)
        text = "".join(lines)
        if lines and lines[0].startswith('"""') and lines[0].rstrip().endswith('"""') and text.count(lines[0]) == 1:
            body = lines[0].rstrip()[3:-3].rstrip(".")
            groups.append([{"file": fname, "old": lines[0],
                            "new": '"""%s.\n\nPart of the %s app; behaviour is described in its README.\n"""\n' % (body, app)}])
        for i, ln in enumerate(lines[:-1]):
            m = DEF.match(ln)
            if not m or lines[i + 1].lstrip().startswith(('"""', "'''")) or text.count(ln) != 1:
                continue
            if lines[i + 1].strip() == "":
                continue
            kind = "Class holding" if m.group(2) == "class" else "Helper:"
            doc = '%s    """%s %s."""\n' % (m.group(1), kind, _words(m.group(3)))
            groups.append([{"file": fname, "old": ln, "new": ln + doc}])
    return groups


if __name__ == "__main__":
    json.dump(pool(sys.argv[1]), sys.stdout, indent=1)
    sys.stdout.write("\n")
