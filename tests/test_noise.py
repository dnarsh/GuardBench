"""Every noise pool must apply cleanly and leave the app's own tests green (noise is benign)."""
import glob
import json
import os
import shutil

import pytest

from guardbench import cli
from guardbench.build import noise_applies, render_all
from guardbench.validate import run_tests

POOLS = sorted(glob.glob(os.path.join(cli.REPO_ROOT, "noise", "*.json")))


def test_every_app_has_a_noise_pool():
    apps = {n for n in os.listdir(os.path.join(cli.REPO_ROOT, "apps"))
            if os.path.isdir(os.path.join(cli.REPO_ROOT, "apps", n))}
    assert apps == {os.path.basename(p)[:-5] for p in POOLS}


@pytest.mark.parametrize("pool", POOLS, ids=lambda p: os.path.basename(p)[:-5])
def test_noise_pool_applies_and_app_tests_still_pass(pool, tmp_path):
    app = os.path.basename(pool)[:-5]
    src = os.path.join(cli.REPO_ROOT, "apps", app)
    with open(pool, encoding="utf-8") as fh:
        noise = json.load(fh)
    assert len(noise) >= 15
    assert noise_applies(src, noise) is None
    work = str(tmp_path / app)
    shutil.copytree(src, work, ignore=shutil.ignore_patterns("__pycache__"))
    for name, text in render_all(src, noise).items():
        with open(os.path.join(work, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    module = [n[:-3] for n in os.listdir(work) if n.startswith("test_") and n.endswith(".py")][0]
    status, out = run_tests(work, module, 60)
    assert status == "pass", out
