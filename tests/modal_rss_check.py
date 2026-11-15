"""Run the RSS measurement tests on Linux (Modal, GNU time) and a mutation check (rc2, F6).

    modal run tests/modal_rss_check.py

1. tests/test_rss_measurement.py with the real measure() must pass.
2. Mutation: replace measure() by a direct fork (os.wait4 ru_maxrss, the v1.0.0 method). On
   Linux the parent-ballast isolation test must then FAIL, proving it detects inheritance.
"""
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent.parent
image = (modal.Image.debian_slim(python_version="3.12").apt_install("time")
         .add_local_dir(ROOT / "benchmarks", "/w/benchmarks", ignore=["__pycache__"])
         .add_local_dir(ROOT / "tests", "/w/tests", ignore=["__pycache__"]))
app = modal.App("colorframe-rss-check", image=image)

MUTANT = r'''
import os, subprocess, sys, time, unittest
sys.path.insert(0, "/w/tests"); sys.path.insert(0, "/w/benchmarks")
import run_benchmarks as rb, test_rss_measurement as t
def direct(cmd):
    t0 = time.perf_counter_ns(); p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    _, st, ru = os.wait4(p.pid, 0); err = p.stderr.read().decode(); p.stderr.close()
    return {"wall_ms": (time.perf_counter_ns()-t0)/1e6, "peak_rss_mb": ru.ru_maxrss/1024.0,
            "exit": os.waitstatus_to_exitcode(st), "stderr": err}
rb.measure = direct
r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(t.ParentBallastIsolation))
sys.exit(0 if not r.wasSuccessful() else 1)   # success of the mutation check = the test FAILED
'''


@app.function(cpu=1.0, memory=4096, timeout=600)
def check() -> tuple[int, str]:
    import subprocess
    out, rc = [], 0
    for name, cmd in [("python", "python3 --version"), ("time", "/usr/bin/time --version 2>&1 | head -1"),
                      ("real measure()", "python3 tests/test_rss_measurement.py"),
                      ("mutant direct-fork measure() must fail isolation", f"python3 -c '{MUTANT}'")]:
        p = subprocess.run(cmd, shell=True, cwd="/w", capture_output=True, text=True)
        out.append(f"== {name}: exit {p.returncode}\n{p.stdout[-2500:]}{p.stderr[-2500:]}")
        rc = rc or p.returncode
    return rc, "\n".join(out)


@app.local_entrypoint()
def main():
    rc, log = check.remote()
    print(log)
    if rc:
        raise SystemExit(rc)
