#!/usr/bin/env python3
"""RQ1 evaluation (v1.0.1, D-021): planted-ORF recovery against true-sample support ceilings.

For each RQ1 workload (`generated/rq1_r*`) one implementation is run with `--policy both` and the
workload's own limits (outputs are byte-identical across implementations once
tests/cross_language.py passes). Every planted ORF is classified from the observed colours of its
walk's nodes and its true sample set T:

  all_local              every node has >= 1 colour                 (what permissive can see)
  all_shared             one colour is on every node                (what strict can see)
  true_local             every node has >= 1 colour in T
  true_shared            one colour in T is on every node
  spurious_local_only    all_local but not true_local    (local support exists only via noise)
  spurious_shared_only   all_shared but not true_shared  (the shared colour is not a true sample)

Policy ceilings: strict -> true_shared, permissive -> true_local. Per (workload, policy):

  recovered                       planted ORFs found with identical (path, start, sequence)
  true_ceiling                    planted ORFs meeting the policy's true-support ceiling
  recovered_within_true_ceiling   recovered and meeting the ceiling
  recovered_via_spurious_only     recovered although the ceiling is not met (noise-enabled)
  candidates / extra_candidates / fragmented   output volume

"Recovery" is synthetic ground-truth recovery in a simplified graph model; a recovered candidate
is not a validated gene. Extra candidates are real ORFs in synthetic background sequence.

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

COLUMNS = ["workload", "replicate", "condition", "p_true_observation", "p_spurious_colour", "policy",
           "planted", "recovered", "true_ceiling", "recovered_within_true_ceiling",
           "recovered_via_spurious_only", "all_local_support", "all_shared_support",
           "true_local_support", "true_shared_support", "spurious_local_only", "spurious_shared_only",
           "candidates", "extra_candidates", "fragmented", "search_states", "exhaustive",
           "state_limit_hit"]


def support_flags(node_colours, true_samples):
    """Classify one planted walk from its nodes' observed colour sets and its true sample set."""
    true_samples = set(true_samples)
    all_local = all(bool(c) for c in node_colours)
    true_local = all(bool(c & true_samples) for c in node_colours)
    shared = set.intersection(*map(set, node_colours)) if node_colours else set()
    all_shared = bool(shared)
    true_shared = bool(shared & true_samples)
    return {"all_local": all_local, "all_shared": all_shared,
            "true_local": true_local, "true_shared": true_shared,
            "spurious_local_only": all_local and not true_local,
            "spurious_shared_only": all_shared and not true_shared}


def policy_ceiling(policy, flags):
    """The true-support condition a planted ORF must meet to be recoverable under `policy`."""
    return flags["true_shared"] if policy == "strict" else flags["true_local"]


def _read(path):
    lines = Path(path).read_text().splitlines()
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def evaluate(wdir, impl):
    """Return one row per policy for workload directory `wdir`."""
    wdir = Path(wdir)
    params = json.loads((wdir / "params.json").read_text())
    planted = _read(wdir / "planted.tsv")
    nodes = {r["node_id"]: (set() if r["colors"] == "." else set(map(int, r["colors"].split(","))))
             for r in _read(wdir / "nodes.tsv")}
    toks = params["cli_args"].split()
    limits = [t for i, t in enumerate(toks) if t != "--policy" and (i == 0 or toks[i - 1] != "--policy")]
    with tempfile.TemporaryDirectory() as t:
        c, s = Path(t) / "c.tsv", Path(t) / "s.tsv"
        subprocess.run(IMPLS[impl] + ["--nodes", str(wdir / "nodes.tsv"), "--edges", str(wdir / "edges.tsv"),
                                      "--out", str(c), "--summary", str(s), "--policy", "both"] + limits,
                       check=True, capture_output=True)
        cands, summ = _read(c), {r["policy"]: r for r in _read(s)}
    flags = [support_flags([nodes[v] for v in p["path"].split(">")], set(map(int, p["true_samples"].split(","))))
             for p in planted]
    keys = [(p["path"], p["start_offset"], p["sequence"]) for p in planted]
    rows = []
    for pol in ("strict", "permissive"):
        pc = [r for r in cands if r["policy"] == pol]
        found = {(r["path"], r["start_offset"], r["sequence"]) for r in pc}
        rec = [k in found for k in keys]
        ceil = [policy_ceiling(pol, f) for f in flags]
        rows.append({
            "workload": wdir.name, "replicate": params.get("replicate", ""), "condition": params.get("condition", ""),
            "p_true_observation": params.get("p_true_observation", ""),
            "p_spurious_colour": params.get("p_spurious_colour", ""), "policy": pol,
            "planted": len(planted), "recovered": sum(rec), "true_ceiling": sum(ceil),
            "recovered_within_true_ceiling": sum(r and c for r, c in zip(rec, ceil)),
            "recovered_via_spurious_only": sum(r and not c for r, c in zip(rec, ceil)),
            "all_local_support": sum(f["all_local"] for f in flags),
            "all_shared_support": sum(f["all_shared"] for f in flags),
            "true_local_support": sum(f["true_local"] for f in flags),
            "true_shared_support": sum(f["true_shared"] for f in flags),
            "spurious_local_only": sum(f["spurious_local_only"] for f in flags),
            "spurious_shared_only": sum(f["spurious_shared_only"] for f in flags),
            "candidates": len(pc), "extra_candidates": len(pc) - sum(rec),
            "fragmented": sum(r["status"] == "fragmented_support" for r in pc),
            "search_states": summ[pol]["search_states"], "exhaustive": summ[pol]["exhaustive"],
            "state_limit_hit": summ[pol]["state_limit_hit"],
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", default="rust")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    wdirs = sorted(d for d in (ROOT / "generated").iterdir()
                   if d.name.startswith("rq1_r") and (d / "planted.tsv").exists())
    rows = [r for w in wdirs for r in evaluate(w, a.impl)]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        f.write("\t".join(COLUMNS) + "\n")
        for r in rows:
            f.write("\t".join(str(r[k]) for k in COLUMNS) + "\n")
    print(f"wrote {len(rows)} rows ({len(wdirs)} workloads) to {a.out}")


if __name__ == "__main__":
    main()
