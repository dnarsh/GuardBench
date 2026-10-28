"""validate's runner: process-tree kill, scrubbed env, no network, bounded output."""
import os
import socket
import sys
import time

from guardbench import validate as V

HEAD = "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_it(self):\n"


def _run(tmp_path, body, timeout=20):
    (tmp_path / "test_x.py").write_text(HEAD + "".join("        %s\n" % ln for ln in body.splitlines()),
                                        newline="\n")
    return V.run_tests(str(tmp_path), "test_x", timeout)


def test_timeout_kills_a_sleeping_grandchild(tmp_path):
    beat = tmp_path.parent / (tmp_path.name + "-beat.txt")
    grandchild = ("import time\nwhile True:\n    open(%r, 'a').write('x')\n    time.sleep(0.1)\n" % str(beat))
    body = ("import subprocess, sys, time\n"
            "subprocess.Popen([sys.executable, '-c', %r])\n"
            "time.sleep(120)" % grandchild)
    status, _ = _run(tmp_path, body, timeout=3)
    assert status == "timeout"
    assert beat.exists(), "grandchild never started; the test proves nothing"
    size = beat.stat().st_size
    time.sleep(1.0)
    assert beat.stat().st_size == size, "grandchild still writing after the timeout"


def test_environment_is_scrubbed_and_home_is_a_temp_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("GB_SECRET_TOKEN", "hunter2")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    real_home = os.path.expanduser("~")
    status, out = _run(tmp_path, "import os\n"
                       "self.assertNotIn('GB_SECRET_TOKEN', os.environ)\n"
                       "self.assertNotIn('PYTHONPATH', os.environ)\n"
                       "self.assertNotEqual(os.path.realpath(os.environ['HOME']), os.path.realpath(%r))\n"
                       "self.assertNotEqual(os.path.realpath(os.environ['HOME']), os.path.realpath(os.getcwd()))\n"
                       % real_home)
    assert status == "pass", out


def test_outgoing_connections_are_refused(tmp_path):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    srv.settimeout(0.5)
    port = srv.getsockname()[1]
    try:
        status, out = _run(tmp_path, "import socket\n"
                           "with self.assertRaises(OSError):\n"
                           "    socket.create_connection(('127.0.0.1', %d), timeout=2)\n"
                           "s = socket.socket()\n"
                           "with self.assertRaises(OSError):\n"
                           "    s.connect(('127.0.0.1', %d))\n" % (port, port))
        assert status == "pass", out
        try:
            srv.accept()
            connected = True
        except socket.timeout:
            connected = False
        assert not connected
    finally:
        srv.close()


def test_runaway_output_is_cut_off(tmp_path):
    t0 = time.time()
    status, out = _run(tmp_path, "import sys\n"
                       "chunk = 'x' * 65536\n"
                       "for _ in range(4000):\n"
                       "    sys.stdout.write(chunk)\n"
                       "    sys.stdout.flush()\n", timeout=60)
    assert status == "error"
    assert "output limit" in out
    assert len(out) <= V.MAX_OUTPUT + 200
    assert time.time() - t0 < 30


def test_normal_runs_still_work(tmp_path):
    assert _run(tmp_path, "self.assertTrue(True)")[0] == "pass"
    assert _run(tmp_path, "self.assertTrue(False)")[0] == "fail"
