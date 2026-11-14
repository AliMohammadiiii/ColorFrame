#!/usr/bin/env python3
"""Shared conformance runner: executes an implementation on every fixture case and
compares outputs byte-for-byte with the hand-derived expectations.

    python3 tests/run_cases.py --impl python        # or cpp, rust, all
    python3 tests/run_cases.py --impl rust --case G08

Valid cases:   exit 0, candidates.tsv and summary.tsv byte-identical to expected_*.tsv.
Invalid cases: exit 2, first stderr line starts with "ERROR <CODE>:", no output files written.
Usage case:    missing --policy -> exit 64.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "fixtures" / "cases"
IMPLS = {
    "python": [sys.executable, str(ROOT / "python" / "colorframe.py")],
    "cpp": [str(ROOT / "cpp" / "build" / "colorframe")],
    "rust": [str(ROOT / "rust" / "target" / "release" / "colorframe")],
}


def run_case(cmd, case: Path, tmp: Path):
    out, summ = tmp / "candidates.tsv", tmp / "summary.tsv"
    for f in (out, summ):
        if f.exists():
            f.unlink()
    args = (case / "args.txt").read_text().split()
    full = cmd + ["--nodes", str(case / "nodes.tsv"), "--edges", str(case / "edges.tsv"),
                  "--out", str(out), "--summary", str(summ)] + args
    try:
        p = subprocess.run(full, capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, PermissionError) as e:
        return f"cannot execute: {e}"
    except subprocess.TimeoutExpired:
        return "timeout"
    err_file = case / "expected_error.txt"
    if err_file.exists():
        code = err_file.read_text().strip()
        first = (p.stderr.splitlines() or [""])[0]
        if p.returncode != 2:
            return f"expected exit 2 ({code}), got {p.returncode}; stderr={first!r}"
        if not first.startswith(f"ERROR {code}:"):
            return f"expected 'ERROR {code}:', got {first!r}"
        if out.exists() or summ.exists():
            return "output files written despite validation error"
        return None
    if p.returncode != 0:
        return f"exit {p.returncode}; stderr={p.stderr.strip()[:300]!r}"
    for got, exp in ((out, "expected_candidates.tsv"), (summ, "expected_summary.tsv")):
        if not got.exists():
            return f"{got.name} not written"
        if got.read_bytes() != (case / exp).read_bytes():
            diff = subprocess.run(["diff", str(case / exp), str(got)], capture_output=True, text=True).stdout
            return f"{got.name} differs from {exp}:\n{diff}"
    return None


def usage_check(cmd, tmp: Path):
    case = CASES / "G01_single_node_orf"
    p = subprocess.run(cmd + ["--nodes", str(case / "nodes.tsv"), "--edges", str(case / "edges.tsv"),
                              "--out", str(tmp / "c.tsv"), "--summary", str(tmp / "s.tsv")],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 64:
        return f"missing --policy: expected exit 64, got {p.returncode}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", choices=list(IMPLS) + ["all"], required=True)
    ap.add_argument("--case", default="", help="substring filter on case directory names")
    a = ap.parse_args()
    impls = list(IMPLS) if a.impl == "all" else [a.impl]
    cases = sorted(d for d in CASES.iterdir() if d.is_dir() and a.case in d.name)
    failures = 0
    for impl in impls:
        tmp = Path(tempfile.mkdtemp(prefix=f"cf_{impl}_"))
        passed = 0
        for case in cases:
            err = run_case(IMPLS[impl], case, tmp)
            if err:
                failures += 1
                print(f"FAIL [{impl}] {case.name}: {err}")
            else:
                passed += 1
        uerr = usage_check(IMPLS[impl], tmp) if not a.case else None
        if uerr:
            failures += 1
            print(f"FAIL [{impl}] usage: {uerr}")
        print(f"[{impl}] {passed}/{len(cases)} cases passed" + ("" if a.case else f"; usage check {'ok' if not uerr else 'FAILED'}"))
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
