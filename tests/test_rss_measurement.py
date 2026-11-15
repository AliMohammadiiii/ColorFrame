#!/usr/bin/env python3
"""Peak-RSS measurement must not inherit the benchmark harness's own memory (D-020).

On Linux, ru_maxrss of a child forked directly from the harness includes the harness's RSS at
fork time (the high-water mark survives exec); the v1.0.0 Modal run showed a ~51 MB floor for
that reason. run_benchmarks.measure() therefore forks through /usr/bin/time.

rc2 (audit finding F6): no absolute ceiling on the Python interpreter, whose baseline differs by
distribution (13.9 MB on Modal's Debian Python, ~93 MB reported for one venv Python). The
isolation property is tested relative to the same child's own pre-ballast baseline:

  inherited RSS (the bug) adds roughly the parent's RSS, i.e. >= BALLAST_MB;
  TOLERANCE_MB = 25% of BALLAST_MB separates that from ordinary run-to-run jitter (< 5 MB seen).
"""
import shutil
import statistics
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks"))
import run_benchmarks as rb  # noqa: E402

PY = sys.executable
TRUE = shutil.which("true")
BALLAST_MB = 300
TOLERANCE_MB = 0.25 * BALLAST_MB


def peak(cmd, n=3):
    """Median peak RSS (MiB) of n wrapped runs; asserts each run exits 0."""
    vals = []
    for _ in range(n):
        m = rb.measure(cmd)
        assert m["exit"] == 0, m
        vals.append(m["peak_rss_mb"])
    return statistics.median(vals)


class TinyNativeProcess(unittest.TestCase):
    def test_true_is_small(self):
        # A native no-op; any working wrapper reports a few MiB. Generous bound, not a Python limit.
        self.assertLess(peak([TRUE]), 20.0)


class PythonBaseline(unittest.TestCase):
    def test_python_baseline_is_measured(self):
        self.assertGreater(peak([PY, "-c", "pass"]), 0.0)   # no ceiling: distribution-dependent


class AllocationVisibility(unittest.TestCase):
    def test_child_allocation_is_visible(self):
        base = peak([PY, "-c", "pass"])
        big = peak([PY, "-c", "b = bytearray(100*1024*1024); b[::4096] = b'x' * len(b[::4096])"])
        self.assertGreater(big - base, 80.0)


class ParentBallastIsolation(unittest.TestCase):
    def test_child_peak_does_not_grow_with_parent_memory(self):
        cmds = {"true": [TRUE], "python": [PY, "-c", "pass"]}
        before = {k: peak(c) for k, c in cmds.items()}
        ballast = bytearray(BALLAST_MB * 1024 * 1024)
        ballast[::4096] = b"\x01" * len(ballast[::4096])          # touch every page
        try:
            after = {k: peak(c) for k, c in cmds.items()}
        finally:
            del ballast
        for k in cmds:
            with self.subTest(child=k, before=before[k], after=after[k]):
                self.assertLess(after[k] - before[k], TOLERANCE_MB)


class ExitAndWallTime(unittest.TestCase):
    def test_exit_code_and_wall_time_reported(self):
        m = rb.measure([PY, "-c", "import sys; sys.exit(3)"])
        self.assertEqual(m["exit"], 3)
        self.assertGreater(m["wall_ms"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
