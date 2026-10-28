"""Compose a seeded defect with benign noise into one realistic multi-hunk review item.

A spec holds the defect edits (bug and clean variant, exact old/new text). A noise pool is
a list of groups; a group is a list of edits that must be taken together (a rename touches
every call site). Edits are {"file", "old", "new"}; `old` must occur exactly once in the
clean app file. The same deterministic noise selection is applied to both the bug diff and
the clean-twin diff, so the defect hunk is the only difference between the two.
"""
import difflib
import os
import random

GAP = 8  # noise must stay this many lines away from the defect, so hunks never merge
HUNKS = (8, 25)
FILES = (3, 6)


class BuildError(ValueError):
    pass


def _text(app_dir, cache, name):
    if name.startswith("test_") or "/" in name or "\\" in name or name.startswith("."):
        raise BuildError("edits may only touch top-level non-test files: %r" % name)
    if name not in cache:
        with open(os.path.join(app_dir, name), encoding="utf-8", newline="") as fh:
            cache[name] = fh.read()
    return cache[name]


def _site(app_dir, cache, e):
    t = _text(app_dir, cache, e["file"])
    i = t.find(e["old"])
    if not e["old"] or i < 0:
        raise BuildError("%s: edit text not found: %r" % (e["file"], e["old"][:50]))
    if t.find(e["old"], i + 1) >= 0:
        raise BuildError("%s: edit text is not unique: %r" % (e["file"], e["old"][:50]))
    return e["file"], i, i + len(e["old"]), e["new"]


def _lines(app_dir, cache, site):
    t = _text(app_dir, cache, site[0])
    return t.count("\n", 0, site[1]) + 1, t.count("\n", 0, max(site[1], site[2] - 1)) + 1


def _render(app_dir, cache, sites):
    """Apply sites; return ({file: new text}, [(site, new_start_offset)])."""
    out, marks = {}, []
    for name in sorted({s[0] for s in sites}):
        t = _text(app_dir, cache, name)
        mine = sorted((s for s in sites if s[0] == name), key=lambda s: s[1])
        for a, b in zip(mine, mine[1:]):
            if a[2] > b[1]:
                raise BuildError("%s: overlapping edits" % name)
        parts, cur, delta = [], 0, 0
        for s in mine:
            parts += [t[cur:s[1]], s[3]]
            marks.append((s, s[1] + delta))
            delta += len(s[3]) - (s[2] - s[1])
            cur = s[2]
        out[name] = "".join(parts) + t[cur:]
    return out, marks


def _diff(app_dir, cache, new_texts):
    out = {}
    for name, new in new_texts.items():
        d = list(difflib.unified_diff(_text(app_dir, cache, name).split("\n"), new.split("\n"),
                                      "a/" + name, "b/" + name, n=3, lineterm=""))
        if d:
            out[name] = "\n".join(d) + "\n"
    return out


def _count(patches):
    return sum(ln.startswith("@@") for p in patches.values() for ln in p.split("\n"))


def noise_applies(app_dir, noise):
    """None if every noise group can be located and no two edits overlap, else a message."""
    cache = {}
    try:
        _render(app_dir, cache, [_site(app_dir, cache, e) for g in noise for e in g])
    except BuildError as e:
        return str(e)
    return None


def _test_module(app_dir):
    mods = [n[:-3] for n in os.listdir(app_dir) if n.startswith("test_") and n.endswith(".py")]
    if len(mods) != 1:
        raise BuildError("app needs exactly one test_*.py module, found %s" % mods)
    return mods[0]


def build_item(app_dir, spec, noise):
    """Return {"defect.json": dict, "bug.patch": str, "clean.patch": str, "stats": dict}."""
    cache = {}
    bug = [_site(app_dir, cache, e) for e in spec["bug"]]
    clean = [_site(app_dir, cache, e) for e in spec["clean"]]
    regions = [(s[0],) + _lines(app_dir, cache, s) for s in bug + clean]

    def feasible(g):
        try:
            sites = [_site(app_dir, cache, e) for e in g]
        except BuildError:
            return None
        for s in sites:
            l1, l2 = _lines(app_dir, cache, s)
            if any(s[0] == f and l1 <= e + GAP and l2 >= b - GAP for f, b, e in regions):
                return None
        return sites

    groups = [s for s in (feasible(g) for g in noise) if s]
    for salt in range(100):
        rng = random.Random("%s:%d" % (spec["id"], salt))
        rng.shuffle(groups)
        target = rng.randint(HUNKS[0] + 1, 16)
        chosen = []
        for g in groups:
            trial = [s for c in chosen for s in c] + g
            try:
                texts, _ = _render(app_dir, cache, bug + trial)
            except BuildError:
                continue
            if len(texts) <= FILES[1] and _count(_diff(app_dir, cache, texts)) <= target:
                chosen.append(g)
        flat = [s for c in chosen for s in c]
        bug_texts, marks = _render(app_dir, cache, bug + flat)
        bug_patches = _diff(app_dir, cache, bug_texts)
        n = _count(bug_patches)
        if HUNKS[0] <= n <= HUNKS[1] and FILES[0] <= len(bug_patches) <= FILES[1]:
            break
    else:
        raise BuildError("%s: cannot reach %s hunks over %s files; noise pool too small"
                         % (spec["id"], HUNKS, FILES))
    clean_patches = _diff(app_dir, cache, _render(app_dir, cache, clean + flat)[0])
    spots = []  # (start line, end line) of the defect in the patched file
    for s, off in marks:
        if s in bug and s[0] == spec["file"]:
            t = bug_texts[s[0]]
            if s[3]:
                spots.append((t.count("\n", 0, off) + 1, t.count("\n", 0, off + max(len(s[3]) - 1, 0)) + 1))
            else:
                ln = t.count("\n", 0, off) + 1
                spots.append((max(ln - 1, 1), ln))
    if not spots:
        raise BuildError("%s: spec['file'] must be one of the bug edits' files" % spec["id"])
    join = lambda ps: "".join(ps[k] for k in sorted(ps))
    return {
        "defect.json": {"id": spec["id"], "app": spec["app"], "class": spec["class"],
                        "test_module": _test_module(app_dir), "file": spec["file"],
                        "start": min(a for a, _ in spots), "end": max(b for _, b in spots)},
        "bug.patch": join(bug_patches),
        "clean.patch": join(clean_patches),
        "stats": {"hunks": n, "files": len(bug_patches), "noise_groups": len(chosen)},
    }


def write_items(spec_paths, out_root, noise_dir, apps_dir):
    """Build every spec file into out_root/defects/<id>/; returns an exit code."""
    import json
    bad = 0
    for sp in spec_paths:
        with open(sp, encoding="utf-8") as fh:
            spec = json.load(fh)
        try:
            with open(os.path.join(noise_dir, spec["app"] + ".json"), encoding="utf-8") as fh:
                noise = json.load(fh)
            item = build_item(os.path.join(apps_dir, spec["app"]), spec, noise)
        except (BuildError, OSError, KeyError) as e:
            print("FAIL %s: %s" % (spec.get("id", sp), e))
            bad += 1
            continue
        d = os.path.join(out_root, "defects", spec["id"])
        os.makedirs(d, exist_ok=True)
        for name in ("bug.patch", "clean.patch"):
            with open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(item[name])
        with open(os.path.join(d, "defect.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(item["defect.json"], fh, indent=2)
            fh.write("\n")
        print("ok   %s %s" % (spec["id"], item["stats"]))
    return 1 if bad else 0


def render_all(app_dir, noise):
    """{file: text} with every noise group applied (raises BuildError if one cannot be)."""
    cache = {}
    return _render(app_dir, cache, [_site(app_dir, cache, e) for g in noise for e in g])[0]
