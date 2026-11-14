# ColorFrame Algorithm Specification

**Status:** Frozen for v1 (spec version `1.0`). Any change requires a `DECISION_LOG.md` entry
approved by the project lead and a spec-version bump.

This document is **authoritative**. The Python, C++17 and Rust implementations must follow it
exactly; where an implementation and this document disagree, the implementation is wrong.
Every counter in the run summary is defined here so that the three implementations can be
compared record-for-record, not only by candidate count.

---

## 1. Problem statement

Given a small directed sequence graph whose nodes carry DNA and sample colours, enumerate every
forward-strand open reading frame (ORF) that

1. starts with `ATG`,
2. ends with the first in-frame stop codon (`TAA`, `TAG`, `TGA`) after that start,
3. is spelled by a walk through the graph that respects the declared edge overlaps, and
4. is admissible under the selected colour-support policy,

subject to explicit, configurable search bounds. Every place where a bound cuts the search is
counted, so a bounded search is never reported as exhaustive.

This is a **simplified model**, not a coloured de Bruijn graph implementation, and not a gene
caller (see `LIMITATIONS.md`).

## 2. Graph model

A graph `G` (identified by `graph_id`) has:

- **Nodes** `v` with an identifier `id(v)`, a non-empty DNA string `seq(v)` over `{A,C,G,T}`, and
  a colour set `col(v) ⊆ ℕ` (possibly empty).
- **Directed edges** `(u → v, ov)` with an overlap length `ov`. Self-loops are allowed.
  At most one edge per ordered pair `(u, v)`.

### 2.1 Overlap rules

For every edge `(u → v, ov)`:

- `0 ≤ ov ≤ len(seq(u))` and `ov < len(seq(v))` (so that entering `v` always adds ≥ 1 base);
- `suffix(seq(u), ov) == prefix(seq(v), ov)`;
- **all edges of one graph share the same overlap** `K` (as in a compacted de Bruijn graph where
  every overlap is `k − 1`). `K = 0` is allowed.

### 2.2 Spelling a walk

A walk `w = (v₁, v₂, …, v_m)` spells

```
spell(w) = seq(v₁) + seq(v₂)[K:] + … + seq(v_m)[K:]
```

i.e. overlap bases are written once, by the upstream node.

### 2.3 Start-position ownership

A base that lies in an overlap region is present in both the upstream and the downstream node.
To report each start exactly once, a start position belongs to exactly one node:

- `startable(u) = [0, len(seq(u)))` if `u` has no outgoing edges;
- `startable(u) = [0, len(seq(u)) − K)` otherwise.

The last `K` bases of a node with successors are owned by each successor (whose prefix spells the
same bases). This attributes the start to the shortest walk that spells it, which is the walk
with the fewest colour constraints. With `K = 0` every position is startable.

## 3. Search parameters

| Parameter | CLI flag | Default | Constraint |
|---|---|---:|---|
| Maximum ORF length (nt, stop codon included) | `--max-orf-nt` | 1200 | ≥ 6 |
| Maximum walk length (node visits) | `--max-path-nodes` | 12 | ≥ 1 |
| Maximum visits of one node within a walk | `--max-node-visits` | 2 | ≥ 1 |
| Maximum search states per graph and policy | `--max-states` | 50000 | ≥ 1 |
| Support policy | `--policy` | (required) | `strict`, `permissive`, `both` |

The bounds are computational safeguards, not biological limits.

## 4. Search procedure

Graphs are processed independently, in ascending byte order of `graph_id`. For `--policy both`,
each graph is searched once with `strict` and once with `permissive`; the two searches share no
state. All string orderings in this document are **byte-wise lexicographic** on ASCII.

### 4.1 Per-search state

```
stats: search_states, max_depth, candidates, start_rejected, color_pruned,
       dead_ends, orf_length_cuts, path_length_cuts, node_visit_cuts  (all 0)
       state_limit_hit = false
walk:   list of node ids (current walk)
visits: map node → number of occurrences in walk
seq:    bases spelled since the start position (the ORF so far)
active: colour intersection over the walk
abort:  false
```

### 4.2 Pseudocode (normative)

```text
SEARCH(G, policy, limits):
    for u in nodes of G sorted by id:
        for s in startable(u) ascending:
            local = seq(u)[s : min(s+3, len(seq(u)))]
            if "ATG" does not start with local: continue        # no frame created
            ENTER(u, start_offset = s, is_start = true)
            if abort: return

ENTER(v, start_offset, is_start):
    if stats.search_states == limits.max_states:
        stats.state_limit_hit = true; abort = true; return
    stats.search_states += 1
    walk.push(v); visits[v] += 1
    stats.max_depth = max(stats.max_depth, len(walk))
    saved_active = active
    active = col(v) if is_start else (active ∩ col(v))

    # colour gate (evaluated on entry, before any base of v is read)
    if policy == strict     and active is empty:  stats.color_pruned += 1; goto LEAVE
    if policy == permissive and col(v) is empty:  stats.color_pruned += 1; goto LEAVE

    contribution = seq(v)[start_offset:] if is_start else seq(v)[K:]
    for b in contribution:
        seq.append(b)
        if len(seq) % 3 == 0:
            codon = last three bases of seq
            if len(seq) == 3:
                if codon != "ATG": stats.start_rejected += 1; goto LEAVE
            else if codon in {TAA, TAG, TGA}:
                EMIT(); goto LEAVE
        if len(seq) >= limits.max_orf_nt:
            stats.orf_length_cuts += 1; goto LEAVE

    # v exhausted, ORF still open
    successors = out-edges of v sorted by target id
    if successors is empty: stats.dead_ends += 1; goto LEAVE
    for w in successors:
        if len(walk) >= limits.max_path_nodes: stats.path_length_cuts += 1; continue
        if visits[w] >= limits.max_node_visits: stats.node_visit_cuts += 1; continue
        ENTER(w, start_offset = 0, is_start = false)
        if abort: goto LEAVE

LEAVE:
    remove the bases this frame appended from seq
    active = saved_active
    visits[v] -= 1; walk.pop()
```

Notes that are part of the specification:

1. **Search state** = one call of `ENTER` that passes the state-limit check. Start frames count.
2. A start frame is created only if the bases of `u` available from `s` are a prefix of `ATG`
   (`"ATG"`, `"AT"` at the last-but-one position, `"A"` at the last position). A start codon that
   spans a node boundary is therefore detected; if the completed first codon is not `ATG`, the
   frame is counted in `start_rejected`.
3. The **reading frame** is implicit: codon boundaries are every third base of `seq`, measured
   from the start codon. Because overlap bases are never duplicated, a cycle whose spelled
   length (`Σ len(seq(v)) − K` per traversal) is not divisible by 3 shifts the frame on each
   traversal; one divisible by 3 preserves it. No special cycle handling exists beyond the
   bounds — this is deliberate and documented in `LIMITATIONS.md`.
4. The search stops at the **first** in-frame stop codon on each walk. Alternative branches are
   not affected: every successor is explored independently.
5. Bound checks for a child happen in the parent, in successor order, before the child is
   entered. Each refused child increments exactly one counter (path-length takes precedence).
6. When the state limit is hit, the whole search for that `(graph, policy)` stops immediately.
   Candidates emitted before that point are reported. Because exploration order is fully
   specified (§4, sorted nodes, ascending offsets, sorted successors, depth-first), the set of
   candidates found before the limit is deterministic across implementations.
7. Iterative (explicit-stack) implementations are allowed only if they reproduce exactly the
   order of `ENTER` calls and counter updates of the recursive pseudocode above.

### 4.3 Emitting a candidate (`EMIT`)

A candidate record contains:

| Field | Value |
|---|---|
| `path` | ids of `walk` joined by `>` |
| `start_offset` | `s` of the start frame (0-based, within the first node) |
| `length_nt` | `len(seq)` (multiple of 3, includes the stop codon) |
| `sequence` | `seq` |
| `support_colors` | `active` (ascending, comma-separated; `.` if empty) |
| `status` | `shared_support` if `active` non-empty, else `fragmented_support` |

`walk` ends at the node from which the last base of the stop codon was read.

Under `strict`, every emitted candidate has `shared_support`. Under `permissive`, a candidate may
be `fragmented_support`: every node on the walk has local colour evidence, but no single sample
colour covers all of them.

### 4.4 Deduplication

Within one `(graph, policy)` search, `(path, start_offset)` uniquely identifies a candidate: a
depth-first search from one start frame visits each walk at most once, and duplicate edges are
rejected at validation. Implementations must nevertheless keep a set keyed by
`(path, start_offset)` and drop any repeat; the number of dropped records must be 0 and is
asserted by the tests (it guards against implementation defects, not against a property of the
algorithm).

### 4.5 Canonical output order

Candidates are sorted by `(graph_id, policy, path, start_offset)` (strings byte-wise, integers
numerically). `candidate_id` is the 1-based rank within each `(graph_id, policy)` group.
Summary rows are sorted by `(graph_id, policy)`.

### 4.6 Summary counters

| Column | Meaning |
|---|---|
| `search_states` | `ENTER` calls that passed the state-limit check |
| `max_depth` | longest walk entered (node visits) |
| `candidates` | emitted candidates |
| `start_rejected` | start frames whose completed first codon was not `ATG` |
| `color_pruned` | frames stopped by the colour gate |
| `dead_ends` | frames that exhausted a node with no successors while the ORF was open |
| `orf_length_cuts` | frames stopped by `max_orf_nt` |
| `path_length_cuts` | children refused by `max_path_nodes` |
| `node_visit_cuts` | children refused by `max_node_visits` |
| `state_limit_hit` | `1` if the state limit stopped the search, else `0` |
| `exhaustive` | `1` iff `orf_length_cuts = path_length_cuts = node_visit_cuts = 0` and `state_limit_hit = 0` |

`dead_ends`, `color_pruned` and `start_rejected` are **not** truncations: they are natural
outcomes of the graph and the policy. `exhaustive = 0` means the bounds hid part of the walk
space, and results must be read as a lower bound.

## 5. Complexity

Let `B` be the maximum out-degree, `P = max_path_nodes`. Per start frame, the number of walks
explored is `O(B^(P−1))` in the worst case (bounded additionally by `max_node_visits` and
`max_states`), and each base is processed in `O(1)` amortised time. Total work is therefore
bounded by `O(max_states · L_max)` where `L_max` is the longest node sequence. Memory is
`O(P + max_orf_nt)` for the walk plus the emitted candidates. The state limit is what makes the
search total on cycle-rich graphs.

## 6. Out of scope for v1

Reverse strand, alternative start codons (`GTG`, `TTG`), longest-ORF selection among nested
in-frame starts (every `ATG` yields its own candidate), minimum ORF length, coding-potential
scoring, frameshift tolerance, partial (start-less or stop-less) gene reporting, and GFA input.
