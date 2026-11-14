#!/usr/bin/env python3
"""Fixture consistency check (no implementation needed).

For every valid case except state-limit cases (whose outcome depends on traversal order),
the brute-force oracle must reproduce expected_candidates.tsv byte-for-byte. Also checks
that every case has exactly one of {expected_error.txt, expected_*.tsv}.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORDER_DEPENDENT = {"B06_state_limit"}
bad = 0
cases = sorted(d for d in (ROOT / "fixtures" / "cases").iterdir() if d.is_dir())
for case in cases:
    has_err = (case / "expected_error.txt").exists()
    has_ok = (case / "expected_candidates.tsv").exists() and (case / "expected_summary.tsv").exists()
    if has_err == has_ok:
        print(f"FAIL {case.name}: needs exactly one of expected_error.txt / expected_*.tsv")
        bad += 1
        continue
    if has_err or case.name in ORDER_DEPENDENT:
        continue
    got = subprocess.run([sys.executable, str(ROOT / "tests" / "oracle_bruteforce.py"), str(case)],
                         capture_output=True, text=True, check=True).stdout
    if got != (case / "expected_candidates.tsv").read_text():
        print(f"FAIL {case.name}: oracle disagrees with hand-derived expected_candidates.tsv")
        bad += 1
print(f"{len(cases) - bad}/{len(cases)} fixture cases consistent")
sys.exit(1 if bad else 0)
