import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import gen_noise  # noqa: E402


def test_pool_documents_undocumented_defs_and_skips_documented_ones_and_tests(tmp_path):
    app = tmp_path / "demo"
    app.mkdir()
    (app / "m.py").write_text('"""Mod."""\n\n\ndef a(x):\n    return x\n\n\ndef b(x):\n    """Has one."""\n    return x\n',
                              newline="\n")
    (app / "test_demo.py").write_text("def test_x():\n    pass\n", newline="\n")
    groups = gen_noise.pool(str(app))
    olds = [g[0]["old"] for g in groups]
    assert olds == ['"""Mod."""\n', "def a(x):\n"]
    assert all(g[0]["file"] == "m.py" for g in groups)
    assert groups[1][0]["new"] == 'def a(x):\n    """Helper: a."""\n'
