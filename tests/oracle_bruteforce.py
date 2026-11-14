#!/usr/bin/env python3
"""Independent brute-force oracle for ColorFrame candidate sets.

Purpose: validate the *hand-derived* expected candidates in fixtures/cases before any
implementation exists. It deliberately uses a different formulation from the DFS in
ALGORITHM_SPEC.md:

    1. enumerate every walk allowed by the path/visit bounds (no sequence logic),
    2. spell the walk from each owned start position,
    3. accept the walk iff the first in-frame stop codon is read from its *last* node.

It checks candidate records only (not DFS counters, and not state-limit behaviour, which
are specific to the traversal order). It is a test tool, not an implementation; it is far
too slow for generated workloads.

Usage: oracle_bruteforce.py CASE_DIR   -> prints candidates.tsv to stdout
"""
import sys
from pathlib import Path

STOPS = {"TAA", "TAG", "TGA"}


def read_tsv(path):
    lines = Path(path).read_text().splitlines()
    return [line.split("\t") for line in lines[1:]]


def parse_args(case_dir):
    toks = Path(case_dir, "args.txt").read_text().split()
    opts = {"--max-orf-nt": 1200, "--max-path-nodes": 12, "--max-node-visits": 2}
    policy = None
    for i, t in enumerate(toks):
        if t == "--policy":
            policy = toks[i + 1]
        elif t in opts:
            opts[t] = int(toks[i + 1])
    return policy, opts


def candidates_for_graph(nodes, edges, policy, opts):
    seq = {n: s for n, s, _ in nodes}
    col = {n: (set() if c == "." else set(map(int, c.split(",")))) for n, _, c in nodes}
    succ = {n: [] for n in seq}
    K = 0
    for s, t, ov in edges:
        succ[s].append(t)
        K = ov
    out = []
    # 1. enumerate walks from every node
    def walks(prefix, visits):
        yield list(prefix)
        if len(prefix) >= opts["--max-path-nodes"]:
            return
        for t in succ[prefix[-1]]:
            if visits.get(t, 0) >= opts["--max-node-visits"]:
                continue
            visits[t] = visits.get(t, 0) + 1
            prefix.append(t)
            yield from walks(prefix, visits)
            prefix.pop()
            visits[t] -= 1

    for u in seq:
        n_start = len(seq[u]) - (K if succ[u] else 0)
        for walk in walks([u], {u: 1}):
            # node-of-origin for each spelled base
            spelled, owner = [], []
            for i, v in enumerate(walk):
                part = seq[v] if i == 0 else seq[v][K:]
                spelled.extend(part)
                owner.extend([i] * len(part))
            for s in range(n_start):
                orf = spelled[s:]
                if "".join(orf[:3]) != "ATG":
                    continue
                stop_end = None
                for j in range(3, len(orf) - 2, 3):
                    if "".join(orf[j:j + 3]) in STOPS:
                        stop_end = j + 3
                        break
                if stop_end is None or stop_end > opts["--max-orf-nt"]:
                    continue
                if owner[s + stop_end - 1] != len(walk) - 1:
                    continue  # stop not in last node: a shorter walk owns this candidate
                inter = set.intersection(*(col[v] for v in walk))
                if policy == "strict" and not inter:
                    continue
                if policy == "permissive" and any(not col[v] for v in walk):
                    continue
                status = "shared_support" if inter else "fragmented_support"
                colors = ",".join(map(str, sorted(inter))) if inter else "."
                out.append((">".join(walk), s, stop_end, "".join(orf[:stop_end]), colors, status))
    out.sort(key=lambda r: (r[0].encode(), r[1]))
    return out


def main(case_dir):
    policy, opts = parse_args(case_dir)
    nodes, edges = {}, {}
    for g, n, s, c in read_tsv(Path(case_dir, "nodes.tsv")):
        nodes.setdefault(g, []).append((n, s, c))
    for g, s, t, ov in read_tsv(Path(case_dir, "edges.tsv")):
        edges.setdefault(g, []).append((s, t, int(ov)))
    policies = ["permissive", "strict"] if policy == "both" else [policy]
    print("graph_id\tpolicy\tcandidate_id\tpath\tstart_offset\tlength_nt\tsequence\tsupport_colors\tstatus")
    for g in sorted(nodes, key=str.encode):
        for p in policies:
            for i, r in enumerate(candidates_for_graph(nodes[g], edges.get(g, []), p, opts), 1):
                print("\t".join(map(str, (g, p, i) + r)))


if __name__ == "__main__":
    main(sys.argv[1])
