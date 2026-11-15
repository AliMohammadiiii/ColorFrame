#!/usr/bin/env python3
"""Deterministic workload generator for ColorFrame benchmarks (base seed 42).

Every workload gets its own RNG, ``random.Random(f"42:{name}")`` (string seeding is
deterministic across platforms in CPython >= 3.2), so adding or changing one workload never
changes another. Output per workload, in ``generated/<name>/``:

    nodes.tsv, edges.tsv   input files (INPUT_OUTPUT_SCHEMA.md), overlap K = 0 (D-010)
    planted.tsv            ORFs written into the graph on purpose (known candidates)
    params.json            every generation parameter + realised statistics + CLI args

Workload families
-----------------
Search limits: perf_* and rq1_* use --max-states 1000000 (far above what they need, so the
state limit never binds and size scaling is not confounded by truncation); stress_* sweeps the
state limit itself. All other limits are the defaults.

perf_*    size x branching grid (charter 6.2) on random ACGT sequence, forward edges only
          (acyclic), colour density 0.5. Extension sizes 2000 and 10000 for scaling.
stress_*  cycle-heavy: high branching with backward edges, sequences over {C,G} with ATG
          sprinkled in node interiors, so no stop codon can ever occur in any frame. Every
          walk runs into a bound, which makes the search-state limit the binding constraint.
rq1_r*    RQ1 (v1.0.1): 10 paired replicates x p_true_observation in {0.1..0.9} x {clean, noisy}.
          See build_rq1() for the colour model; structure is fixed within a replicate.

The synthetic sizes are small and say nothing about biological genome scale.
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_SEED = 42
N_SAMPLES = 8                      # sample colours 0..7
STOPS = {"TAA", "TAG", "TGA"}
SENSE = [a + b + c for a in "ACGT" for b in "ACGT" for c in "ACGT"
         if a + b + c not in STOPS and a + b + c != "ATG"]


def out_degree(rng, mean):
    """floor(mean) + Bernoulli(frac(mean)); mean 1.2 -> 1 or 2, mean 2.0 -> 2."""
    base = int(mean)
    return base + (1 if rng.random() < mean - base else 0)


def random_colors(rng, density, samples=range(N_SAMPLES)):
    return {s for s in samples if rng.random() < density}


def build(name, *, n, mean_deg, cyclic, alphabet, density, n_plant, plant_nodes=3,
          window=10, args=""):
    rng = random.Random(f"{BASE_SEED}:{name}")
    ids = [f"v{i:05d}" for i in range(n)]
    lens = [rng.randint(30, 90) for _ in range(n)]

    if alphabet == "ACGT":
        seqs = [[rng.choice("ACGT") for _ in range(L)] for L in lens]
    else:  # stress: C/G background, ATG only in the interior and never followed by A
        seqs = []
        for L in lens:
            s = [rng.choice("CG") for _ in range(L)]
            # Insertions at least 4 apart: "ATGATG" would create an in-frame TGA stop.
            placed = []
            for _ in range(max(1, L // 30)):
                p = rng.randint(1, L - 5)
                if all(abs(p - q) >= 4 for q in placed):
                    s[p:p + 3] = list("ATG")
                    placed.append(p)
            seqs.append(s)

    # edges: forward window (acyclic) or anywhere except self (cyclic)
    succ = []
    for i in range(n):
        if cyclic:
            pool = [j for j in range(n) if j != i]
        else:
            pool = list(range(i + 1, min(n, i + 1 + window)))
        k = min(out_degree(rng, mean_deg), len(pool))
        succ.append(sorted(rng.sample(pool, k)))

    colors = [random_colors(rng, density) for _ in range(n)]

    # plant ORFs along random forward walks on disjoint node sets
    planted, used = [], set()
    attempts = 0
    while len(planted) < n_plant and attempts < 50 * max(1, n_plant):
        attempts += 1
        walk = [rng.randrange(n)]
        while len(walk) < plant_nodes and succ[walk[-1]]:
            walk.append(rng.choice(succ[walk[-1]]))
        if len(walk) < plant_nodes or len(set(walk)) < len(walk) or used & set(walk):
            continue
        first, last = walk[0], walk[-1]
        start = rng.randint(0, lens[first] - 4)
        # positions (node, offset) of the spelled walk from `start`
        pos = [(first, o) for o in range(start, lens[first])]
        for v in walk[1:-1]:
            pos += [(v, o) for o in range(lens[v])]
        # stop codon ends inside the last node, at least 3 bases in
        stop_end = rng.randint(3, lens[last])
        pos += [(last, o) for o in range(stop_end)]
        trim = len(pos) % 3                       # make the ORF a whole number of codons
        if trim:
            pos = pos[trim:]
            start += trim
            if start > lens[first] - 1:
                continue
        codons = ["ATG"] + [rng.choice(SENSE) for _ in range(len(pos) // 3 - 2)] + [rng.choice(sorted(STOPS))]
        orf = "".join(codons)
        for (v, o), b in zip(pos, orf):
            seqs[v][o] = b
        true_samples = set(rng.sample(range(N_SAMPLES), 4))
        for v in walk:
            colors[v] = random_colors(rng, density, sorted(true_samples)) | random_colors(rng, density * 0.25)
        used |= set(walk)
        planted.append({"path": ">".join(ids[v] for v in walk), "start_offset": start,
                        "length_nt": len(orf), "sequence": orf,
                        "true_samples": ",".join(map(str, sorted(true_samples)))})

    if alphabet != "ACGT":
        colors = [{1} for _ in range(n)]          # stress: no colour pruning at all

    d = ROOT / "generated" / name
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "nodes.tsv", "w") as f:
        f.write("graph_id\tnode_id\tsequence\tcolors\n")
        for i in range(n):
            c = ",".join(map(str, sorted(colors[i]))) or "."
            f.write(f"{name}\t{ids[i]}\t{''.join(seqs[i])}\t{c}\n")
    with open(d / "edges.tsv", "w") as f:
        f.write("graph_id\tsource\ttarget\toverlap_nt\n")
        for i in range(n):
            for j in succ[i]:
                f.write(f"{name}\t{ids[i]}\t{ids[j]}\t0\n")
    with open(d / "planted.tsv", "w") as f:
        f.write("path\tstart_offset\tlength_nt\tsequence\ttrue_samples\n")
        for p in planted:
            f.write(f"{p['path']}\t{p['start_offset']}\t{p['length_nt']}\t{p['sequence']}\t{p['true_samples']}\n")
    n_edges = sum(len(s) for s in succ)
    params = {"name": name, "seed": f"{BASE_SEED}:{name}", "n_nodes": n, "target_mean_out_degree": mean_deg,
              "realised_mean_out_degree": round(n_edges / n, 4), "n_edges": n_edges, "cyclic": cyclic,
              "alphabet": alphabet, "colour_density": density, "n_samples": N_SAMPLES,
              "node_length_range": [30, 90], "forward_window": None if cyclic else window,
              "planted_requested": n_plant, "planted": len(planted), "plant_nodes": plant_nodes,
              "total_bases": sum(lens), "cli_args": args, "family": name.split("_")[0], "benchmark": True,
              "planted_colour_model": ("legacy v1.0.0: each true sample w.p. colour_density, plus every sample "
                                       "w.p. 0.25*colour_density; not used for RQ1 claims (D-021)")}
    (d / "params.json").write_text(json.dumps(params, indent=2) + "\n")
    return params


WORKLOADS = []
for n in (50, 200, 500, 2000, 10000):
    for tag, deg in (("low", 1.2), ("high", 2.0)):
        WORKLOADS.append((f"perf_n{n}_{tag}", dict(n=n, mean_deg=deg, cyclic=False, alphabet="ACGT",
                                                   density=0.5, n_plant=max(1, n // 10),
                                                   args="--policy both --max-states 1000000")))
for states in (12500, 50000, 200000, 800000):
    WORKLOADS.append((f"stress_s{states}", dict(n=200, mean_deg=2.0, cyclic=True, alphabet="CG",
                                                density=1.0, n_plant=0,
                                                args=f"--policy strict --max-states {states}")))

# --------------------------------------------------------------------------- RQ1 (v1.0.1, D-021)
RQ1_P_TRUE = (0.1, 0.2, 0.3, 0.5, 0.7, 0.9)
RQ1_REPLICATES = 10
RQ1_CONDITIONS = ("clean", "noisy")
RQ1_SPURIOUS_FACTOR = 0.25          # noisy condition: p_spurious_colour = 0.25 * p_true_observation
RQ1_N_NODES, RQ1_N_PLANT, RQ1_N_TRUE = 500, 100, 4
RQ1_ARGS = "--policy both --max-states 1000000"


def rq1_name(rep, p_true, condition):
    return f"rq1_r{rep:02d}_p{int(round(p_true * 100)):02d}_{condition}"


def _rq1_structure(rep):
    """Everything that is fixed within a replicate: topology, sequences, planted ORFs, true samples.

    Seeded only by the replicate, so all (p, condition) workloads of a replicate share it (paired
    design). Returns ids, seqs, succ, plants (walk indices + record).
    """
    seed = f"{BASE_SEED}:rq1:rep{rep:02d}:structure"
    rng = random.Random(seed)
    n = RQ1_N_NODES
    ids = [f"v{i:05d}" for i in range(n)]
    lens = [rng.randint(30, 90) for _ in range(n)]
    seqs = [[rng.choice("ACGT") for _ in range(L)] for L in lens]
    succ = []
    for i in range(n):
        pool = list(range(i + 1, min(n, i + 11)))
        succ.append(sorted(rng.sample(pool, min(out_degree(rng, 2.0), len(pool)))))
    plants, used, attempts = [], set(), 0
    while len(plants) < RQ1_N_PLANT and attempts < 50 * RQ1_N_PLANT:
        attempts += 1
        walk = [rng.randrange(n)]
        while len(walk) < 3 and succ[walk[-1]]:
            walk.append(rng.choice(succ[walk[-1]]))
        if len(walk) < 3 or len(set(walk)) < 3 or used & set(walk):
            continue
        first, last = walk[0], walk[-1]
        start = rng.randint(0, lens[first] - 4)
        pos = [(first, o) for o in range(start, lens[first])]
        pos += [(walk[1], o) for o in range(lens[walk[1]])]
        pos += [(last, o) for o in range(rng.randint(3, lens[last]))]
        trim = len(pos) % 3
        if trim:
            pos, start = pos[trim:], start + trim
            if start > lens[first] - 1:
                continue
        orf = "".join(["ATG"] + [rng.choice(SENSE) for _ in range(len(pos) // 3 - 2)] + [rng.choice(sorted(STOPS))])
        for (v, o), b in zip(pos, orf):
            seqs[v][o] = b
        truth = sorted(rng.sample(range(N_SAMPLES), RQ1_N_TRUE))
        used |= set(walk)
        plants.append({"walk": walk, "path": ">".join(ids[v] for v in walk), "start_offset": start,
                       "length_nt": len(orf), "sequence": orf, "true_samples": truth})
    return seed, ids, seqs, succ, plants


def build_rq1(rep, p_true, condition, out_root=None):
    """One RQ1 workload. Colour model (all draws independent):

    planted node v of ORF with true samples T:  s in T observed with p_true_observation;
                                                  s not in T added with p_spurious_colour
    background node:                             any sample observed with p_true_observation;
                                                  any other sample added with p_spurious_colour
    clean: p_spurious_colour = 0;  noisy: p_spurious_colour = 0.25 * p_true_observation.
    Common random numbers per replicate: observed sets are nested across p, noisy = clean + noise.
    """
    assert condition in RQ1_CONDITIONS
    name = rq1_name(rep, p_true, condition)
    p_spur = 0.0 if condition == "clean" else RQ1_SPURIOUS_FACTOR * p_true
    seed_struct, ids, seqs, succ, plants = _rq1_structure(rep)
    # Common random numbers: one uniform per (node, sample) for observation and one for noise,
    # seeded per replicate only. Observed sets are therefore nested across p (0.3 subset of 0.5),
    # and noisy = clean + noise exactly.
    tag = f"{BASE_SEED}:rq1:rep{rep:02d}"
    obs_rng, spur_rng = random.Random(tag + ":observation"), random.Random(tag + ":spurious")
    n = len(ids)
    truth_of = {}
    for pl in plants:
        for v in pl["walk"]:
            truth_of[v] = set(pl["true_samples"])
    colors = []
    for v in range(n):
        u_obs = [obs_rng.random() for _ in range(N_SAMPLES)]
        u_spur = [spur_rng.random() for _ in range(N_SAMPLES)]
        truth = truth_of.get(v)
        if truth is not None:      # planted node: true samples observed, non-true samples spurious
            observed = {s for s in truth if u_obs[s] < p_true}
            noise = {s for s in range(N_SAMPLES) if s not in truth and u_spur[s] < p_spur}
        else:                      # background node: any sample observed, others may be spurious
            observed = {s for s in range(N_SAMPLES) if u_obs[s] < p_true}
            noise = {s for s in range(N_SAMPLES) if s not in observed and u_spur[s] < p_spur}
        colors.append(observed | noise)
    true_local = sum(all(colors[v] & set(pl["true_samples"]) for v in pl["walk"]) for pl in plants)
    true_shared = sum(bool(set.intersection(*(colors[v] for v in pl["walk"])) & set(pl["true_samples"]))
                      for pl in plants)

    d = Path(out_root or ROOT / "generated") / name
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "nodes.tsv", "w") as f:
        f.write("graph_id\tnode_id\tsequence\tcolors\n")
        for i in range(n):
            f.write(f"{name}\t{ids[i]}\t{''.join(seqs[i])}\t{','.join(map(str, sorted(colors[i]))) or '.'}\n")
    with open(d / "edges.tsv", "w") as f:
        f.write("graph_id\tsource\ttarget\toverlap_nt\n")
        for i in range(n):
            for j in succ[i]:
                f.write(f"{name}\t{ids[i]}\t{ids[j]}\t0\n")
    with open(d / "planted.tsv", "w") as f:
        f.write("path\tstart_offset\tlength_nt\tsequence\ttrue_samples\n")
        for pl in plants:
            f.write(f"{pl['path']}\t{pl['start_offset']}\t{pl['length_nt']}\t{pl['sequence']}\t"
                    f"{','.join(map(str, pl['true_samples']))}\n")
    n_edges = sum(len(x) for x in succ)
    params = {"name": name, "family": "rq1", "replicate": rep, "condition": condition,
              "p_true_observation": p_true, "p_spurious_colour": p_spur,
              "spurious_factor_noisy": RQ1_SPURIOUS_FACTOR, "n_samples": N_SAMPLES,
              "true_samples_per_orf": RQ1_N_TRUE, "seed_structure": seed_struct,
              "seed_observation": tag + ":observation", "seed_spurious": tag + ":spurious",
              "n_nodes": n, "n_edges": n_edges, "realised_mean_out_degree": round(n_edges / n, 4),
              "planted_requested": RQ1_N_PLANT, "planted": len(plants), "plant_nodes": 3,
              "realised_true_local_support": true_local, "realised_true_shared_support": true_shared,
              "benchmark": rep == 0 and condition == "clean", "cli_args": RQ1_ARGS}
    (d / "params.json").write_text(json.dumps(params, indent=2) + "\n")
    return params


def main(argv):
    only = set(argv[1:])
    for name, kw in WORKLOADS:
        if only and name not in only:
            continue
        p = build(name, **kw)
        print(f"{name:20s} nodes={p['n_nodes']:6d} edges={p['n_edges']:6d} "
              f"mean_deg={p['realised_mean_out_degree']:.2f} planted={p['planted']}")
    n_rq1 = 0
    for rep in range(RQ1_REPLICATES):
        for p_true in RQ1_P_TRUE:
            for cond in RQ1_CONDITIONS:
                name = rq1_name(rep, p_true, cond)
                if only and name not in only and "rq1" not in only:
                    continue
                build_rq1(rep, p_true, cond)
                n_rq1 += 1
    print(f"rq1: {n_rq1} paired workloads ({RQ1_REPLICATES} replicates x {len(RQ1_P_TRUE)} p x {len(RQ1_CONDITIONS)} conditions)")


if __name__ == "__main__":
    main(sys.argv)
