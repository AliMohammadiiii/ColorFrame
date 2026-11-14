#!/usr/bin/env python3
"""Cross-language equivalence on generated workloads.

Runs every available implementation on every workload in generated/ (with the workload's own
CLI arguments from params.json) and requires byte-identical candidates.tsv and summary.tsv.
Performance must not be compared before this passes (charter 10.4).

    python3 tests/cross_language.py [--impls python,cpp,rust] [--only NAME ...] [--out FILE]
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from run_cases import IMPLS  # noqa: E402


def run(impl, wdir: Path, tmp: Path):
    args = json.loads((wdir / "params.json").read_text())["cli_args"].split()
    out, summ = tmp / f"{impl}_c.tsv", tmp / f"{impl}_s.tsv"
    p = subprocess.run(IMPLS[impl] + ["--nodes", str(wdir / "nodes.tsv"), "--edges", str(wdir / "edges.tsv"),
                                      "--out", str(out), "--summary", str(summ)] + args,
                       capture_output=True, text=True, timeout=3600)
    if p.returncode != 0:
        return None, None, f"exit {p.returncode}: {p.stderr.strip()[:200]}"
    return out.read_bytes(), summ.read_bytes(), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impls", default="python,cpp,rust")
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--out", default=None, help="write a TSV of per-workload digests")
    a = ap.parse_args()
    impls = a.impls.split(",")
    wdirs = sorted(d for d in (ROOT / "generated").iterdir() if (d / "params.json").exists())
    if a.only:
        wdirs = [d for d in wdirs if d.name in a.only]
    if not wdirs:
        sys.exit("no workloads in generated/ — run benchmarks/generate_workloads.py first")
    rows, bad = [], 0
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for w in wdirs:
            res = {i: run(i, w, tmp) for i in impls}
            errs = {i: r[2] for i, r in res.items() if r[2]}
            if errs:
                bad += 1
                print(f"FAIL {w.name}: {errs}")
                continue
            ref = res[impls[0]]
            same = all(r[0] == ref[0] and r[1] == ref[1] for r in res.values())
            dc = hashlib.sha256(ref[0]).hexdigest()[:16]
            ds = hashlib.sha256(ref[1]).hexdigest()[:16]
            n = ref[0].count(b"\n") - 1
            print(f"{'OK  ' if same else 'DIFF'} {w.name:18s} candidates={n:7d} cand_sha={dc} summ_sha={ds}")
            if not same:
                bad += 1
                for i, r in res.items():
                    print(f"     {i}: cand_sha={hashlib.sha256(r[0]).hexdigest()[:16]} "
                          f"summ_sha={hashlib.sha256(r[1]).hexdigest()[:16]}")
            rows.append((w.name, ",".join(impls), "identical" if same else "DIFFERENT", n, dc, ds))
    if a.out:
        with open(a.out, "w") as f:
            f.write("workload\timpls\tresult\tcandidate_rows\tcandidates_sha256_16\tsummary_sha256_16\n")
            for r in rows:
                f.write("\t".join(map(str, r)) + "\n")
    print(f"{len(wdirs) - bad}/{len(wdirs)} workloads equivalent across {', '.join(impls)}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
