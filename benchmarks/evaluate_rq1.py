#!/usr/bin/env python3
"""RQ1 evaluation: planted-ORF recovery and extra candidates per support policy.

For every generated workload that has planted ORFs, run one implementation (outputs are
byte-identical across implementations once tests/cross_language.py passes) with
`--policy both` and default limits, then compare with planted.tsv.

Definitions (per workload x policy):
  candidates            all candidate records
  planted               planted ORFs written by the generator
  planted_recovered     planted ORFs found with identical (path, start_offset, sequence)
  locally_supported     planted ORFs whose every node has >= 1 colour (permissive can find them)
  shared_supported      planted ORFs with >= 1 colour on every node of the walk (strict can find them)
  extra_candidates      candidates that are not planted ORFs (background ORFs)
  fragmented            candidates with status fragmented_support

"Extra" candidates are not false positives in a biological sense: background ORFs are real
ORFs in the synthetic sequence. They measure how much additional output a policy produces.

    python3 benchmarks/evaluate_rq1.py --impl rust --out results/rq1_recovery.tsv
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from run_cases import IMPLS  # noqa: E402


def read(path):
    lines = Path(path).read_text().splitlines()
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", default="rust")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = []
    for w in sorted((ROOT / "generated").iterdir()):
        if not (w / "planted.tsv").exists():
            continue
        planted = read(w / "planted.tsv")
        if not planted:
            continue
        params = json.loads((w / "params.json").read_text())
        nodes = {r["node_id"]: r for r in read(w / "nodes.tsv")}
        with tempfile.TemporaryDirectory() as t:
            c, s = Path(t) / "c.tsv", Path(t) / "s.tsv"
            subprocess.run(IMPLS[a.impl] + ["--nodes", str(w / "nodes.tsv"), "--edges", str(w / "edges.tsv"),
                                            "--out", str(c), "--summary", str(s), "--policy", "both"],
                           check=True, capture_output=True)
            cands = read(c)
            summ = {r["policy"]: r for r in read(s)}
        pset = {(p["path"], p["start_offset"], p["sequence"]) for p in planted}

        def colours(v):
            f = nodes[v]["colors"]
            return set() if f == "." else set(f.split(","))
        local = shared = 0
        for p in planted:
            cs = [colours(v) for v in p["path"].split(">")]
            local += all(cs)
            shared += bool(set.intersection(*cs))
        for pol in ("strict", "permissive"):
            pc = [r for r in cands if r["policy"] == pol]
            keys = {(r["path"], r["start_offset"], r["sequence"]) for r in pc}
            rec = len(pset & keys)
            rows.append({
                "workload": w.name, "family": w.name.split("_")[0], "n_nodes": params["n_nodes"],
                "colour_density": params["colour_density"], "policy": pol,
                "candidates": len(pc), "planted": len(pset), "planted_recovered": rec,
                "locally_supported": local, "shared_supported": shared,
                "extra_candidates": len(pc) - rec,
                "fragmented": sum(r["status"] == "fragmented_support" for r in pc),
                "search_states": summ[pol]["search_states"], "color_pruned": summ[pol]["color_pruned"],
                "exhaustive": summ[pol]["exhaustive"],
            })
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        f.write("\t".join(rows[0]) + "\n")
        for r in rows:
            f.write("\t".join(str(v) for v in r.values()) + "\n")
    print(f"wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()
