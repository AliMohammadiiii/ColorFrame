#!/usr/bin/env python3
"""Timing-phase contract (spec v1.1, INPUT_OUTPUT_SCHEMA.md section 4) for every implementation.

Each implementation must write exactly the rows parse, validate, search, canonicalize, write,
total; every value is a non-negative decimal; and total equals the sum of the five phases
(contiguous timestamps), up to the 3-decimal rounding of six printed values.

    python3 tests/test_timing_contract.py [--impls python,cpp,rust]
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from run_cases import IMPLS  # noqa: E402

PHASES = ["parse", "validate", "search", "canonicalize", "write"]
CASES = ["B11_multi_graph", "G08_repeat_revisit", "B01_empty_graph"]


def check(impl, case, tmp):
    d = ROOT / "fixtures" / "cases" / case
    t = tmp / "t.tsv"
    p = subprocess.run(IMPLS[impl] + ["--nodes", str(d / "nodes.tsv"), "--edges", str(d / "edges.tsv"),
                                      "--out", str(tmp / "c.tsv"), "--summary", str(tmp / "s.tsv"),
                                      "--timings", str(t)] + (d / "args.txt").read_text().split(),
                       capture_output=True, text=True)
    if p.returncode != 0:
        return f"exit {p.returncode}: {p.stderr.strip()[:200]}"
    lines = t.read_text().splitlines()
    if lines[0] != "phase\tms":
        return f"bad header {lines[0]!r}"
    rows = [l.split("\t") for l in lines[1:]]
    names = [r[0] for r in rows]
    if names != PHASES + ["total"]:
        return f"rows {names} != {PHASES + ['total']}"
    vals = {n: float(v) for n, v in rows}
    if any(v < 0 for v in vals.values()):
        return f"negative phase: {vals}"
    if abs(vals["total"] - sum(vals[n] for n in PHASES)) > 0.01:
        return f"total {vals['total']} != sum of phases {sum(vals[n] for n in PHASES):.3f}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impls", default="python,cpp,rust")
    impls = ap.parse_args().impls.split(",")
    bad = 0
    with tempfile.TemporaryDirectory() as t:
        for impl in impls:
            for case in CASES:
                err = check(impl, case, Path(t))
                if err:
                    bad += 1
                    print(f"FAIL [{impl}] {case}: {err}")
            print(f"[{impl}] timing contract {'ok' if not bad else 'FAILED'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
