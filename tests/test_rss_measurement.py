#!/usr/bin/env python3
"""Peak-RSS measurement must not inherit the benchmark harness's own memory.

On Linux, ru_maxrss of a child forked directly from the harness includes the harness's RSS at
fork time (the high-water mark survives exec). The v1.0.0 Modal run reported a ~51 MB floor for
that reason (D-020). run_benchmarks.measure() must fork through a small wrapper so a child's peak
reflects the child only. These checks hold on Linux (GNU time) and macOS (BSD time).
"""
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks"))
import run_benchmarks as rb  # noqa: E402

PY = sys.executable


class PeakRssMeasurement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ballast = bytearray(150 * 1024 * 1024)       # make the parent deliberately large
        for i in range(0, len(cls.ballast), 4096):
            cls.ballast[i] = 1

    def test_tiny_process_is_not_inflated_by_parent(self):
        m = rb.measure([shutil.which("true")])
        self.assertEqual(m["exit"], 0)
        self.assertLess(m["peak_rss_mb"], 20.0)

    def test_interpreter_baseline_is_not_inflated_by_parent(self):
        self.assertLess(rb.measure([PY, "-c", "pass"])["peak_rss_mb"], 60.0)

    def test_allocation_is_visible(self):
        base = rb.measure([PY, "-c", "pass"])["peak_rss_mb"]
        big = rb.measure([PY, "-c", "b = bytearray(100*1024*1024); b[::4096] = b'x' * len(b[::4096])"])
        self.assertGreater(big["peak_rss_mb"] - base, 80.0)

    def test_wall_time_and_exit_code_reported(self):
        m = rb.measure([PY, "-c", "import sys; sys.exit(3)"])
        self.assertEqual(m["exit"], 3)
        self.assertGreater(m["wall_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
