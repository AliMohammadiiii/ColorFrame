# Graph Schema v2 — Proposal (NOT IMPLEMENTED; requires Ali's approval)

**Status:** Proposal for review, 2026-11-15. Nothing in this document changes the v1.1
algorithm, schema, fixtures or results. Implementation, if approved, follows the TDD plan in §8.

## 1. Audit of the current model (spec v1.1)

| Element | Current semantics | Consequence for biological validation |
|---|---|---|
| Node colours | a set of sample ids per node | Level-1 evidence only: "this segment occurs in sample s" |
| Edges | `graph_id, source, target, overlap_nt`; **no colours** | an adjacency is assumed to exist in every sample; no Level-2 evidence |
| `strict` | some colour lies in the intersection of all node colour sets of the walk | shared **node** support. It does not show that sample s contains the adjacencies, still less the spelled path (Principles 1–3) |
| `permissive` | every node has ≥ 1 colour | local support. Different nodes may be supported by different samples |
| Orientation | directed, forward strand only; one sequence per node | reverse-strand genes are invisible unless the graph contains reverse-complement nodes |
| Overlap | one uniform `K` per graph | compatible with a compacted de Bruijn graph (`K = k − 1`) |
| Truncation | explicit counters, `exhaustive` flag | unchanged; still required |

**Concrete failure of the current model.** Sample A contains `X→Y→Z`; sample B contains
`W→Y→V`; both contain a repeat-like node `Y`. In the graph, `X→Y→V` exists. If `X`, `Y` and `V`
all happen to be in colour C (from different genomic contexts in C), `strict` accepts `X→Y→V`
with colour C although no sample contains that adjacency sequence. Node colours cannot detect
this. Edge evidence can detect some cases (§3), and only full-sequence evidence (Level 3,
`PATH_LEVEL_EVIDENCE_PROTOCOL.md`) can confirm a path.

## 2. Design principles

1. **Backward compatibility.** v1 inputs (no edge-evidence file) keep exactly the v1.1 meaning
   and byte-identical outputs. Synthetic fixtures are never edited.
2. **Absent evidence is not negative evidence.** "Edge evidence not recorded" (v1 input) and
   "edge observed in no sample" (v2 input) are distinct states.
3. **Evidence stays out of the search core where possible.** The graph carries Level-1 and
   Level-2 evidence. Level-3 (full path) and Level-4 (CDS) evidence are evaluated after the
   search by the evaluation layer, against references, assemblies or reads.
4. **Smallest change that makes Level-2 evidence expressible.**

## 3. Proposed extension: a separate `edge_support.tsv`

`edges.tsv` stays unchanged. Edge evidence goes in an optional file, passed with
`--edge-support FILE`:

```
graph_id  source  target  sample_id  evidence_type  support_count  evidence_source
```

| Column | Meaning |
|---|---|
| `graph_id, source, target` | must match an edge in `edges.tsv` (otherwise validation error) |
| `sample_id` | colour id; must be declared in the sample manifest |
| `evidence_type` | `reference` (complete sample reference), `assembly` (sample assembly), `reads` (read-derived junction k-mer), `simulated` (simulator provenance) |
| `support_count` | ≥ 1; number of supporting observations (e.g. junction (k+1)-mer count); 1 for reference/assembly |
| `evidence_source` | file or accession it came from (provenance) |

Several rows per (edge, sample) are allowed, one per evidence type. **Definition of an observed
edge in a compacted DBG:** the edge `u→v` with overlap `k−1` spells a unique `(k+1)`-mer across
the junction. The edge is observed in sample s when that `(k+1)`-mer occurs in s's evidence
source. This is checkable for references, assemblies and reads without trusting graph
construction.

**Why a separate file rather than an `edge_colors` column:** it keeps v1 `edges.tsv` byte-stable,
records evidence type and provenance, and allows multiple evidence sources per sample.

## 4. Proposed policies (versioned, additive)

| Policy | Rule | Evidence level | Status |
|---|---|---|---|
| `strict` | unchanged (shared **node** colour) | 1 | v1.1, kept; reported as "shared node support" |
| `permissive` | unchanged | 1 | v1.1, kept |
| `strict_edge` (new) | some sample s lies on **every node and every traversed edge** (edge evidence of any type for s) | 1 + 2 | proposed |

`strict_edge` prunes like `strict`, intersecting node and edge colour sets at each step. It
requires `--edge-support`; without it, the CLI refuses the policy (usage error) rather than
silently assuming all edges supported.

**`strict_edge` is still not path support.** Consecutive junctions supported in s do not prove
the whole spelled sequence is contiguous in s, because repeats can link two locally supported
junctions (Principle 2). Path support stays Level 3 and is decided outside the search.

New per-candidate output columns (v2 output only; v1 runs unchanged):
`edge_shared_colors` (sorted ids supporting all traversed edges, `.` if none) and
`edge_evidence` (`complete` | `partial` | `none` | `untracked`).

## 5. Unitig colour variation (Bifrost)

In Bifrost, colours are attached to individual k-mer positions of a unitig, so colours can
change along one unitig (verification against Bifrost's code and documentation: see
`PRIOR_ART_UPDATE.md`). Taking the union over a unitig would assign a sample to k-mers it does
not contain, which is artificial support.

**Proposal: split unitigs at colour-change boundaries.**
- For unitig `U` with k-mers `κ1 … κm`, let `C(κi)` be each k-mer's colour set. Cut between
  `κi` and `κi+1` whenever `C(κi) ≠ C(κi+1)`.
- Each segment covering k-mers `κa … κb` becomes a node with sequence `U[a .. b+k−1]` and colour
  set `C(κa)` (uniform within the segment).
- Consecutive segments become an edge with overlap `k−1`. Its edge evidence is the junction
  `(k+1)`-mer, checked per sample as in §3.
- The node count grows only where colours change. Uniform `K = k−1` is preserved, so v1.1's
  start-ownership rule still applies.

Node colour then means "every k-mer of this node occurs in s", which is exact at k-mer level.

## 6. Orientation (bidirected → directed)

Bifrost graphs are bidirected: each unitig can be read forward or as its reverse complement,
and edges connect oriented ends. ColorFrame searches directed forward strands.

**Minimal, defensible conversion: oriented doubling.**
- Every unitig/segment `u` becomes two directed nodes, `u+` (sequence) and `u−` (reverse
  complement), with the same colour set.
- Every bidirected edge yields a directed edge plus its reverse-complement mirror
  (`a+→b+` implies `b−→a−`).
- A forward-strand ORF search over the doubled graph then covers both genomic strands. A gene on
  the reverse strand appears as a forward ORF on `−` nodes.
- Each genomic ORF is found once on its coding strand. Candidates are reported with oriented node
  ids, so strand is explicit and nothing is silently dropped.
- Edge case: self-reverse-complementary k-mers and palindromic unitigs map `u+` and `u−` to
  identical sequences. These are kept as two nodes and flagged in adapter diagnostics.

What this does **not** claim: alternative start codons (GTG/TTG), frameshifts, introns, partial
genes at graph tips. These remain outside v1/v2 (`VALIDATION_LIMITATIONS.md`).

## 7. What does not change

Traversal order, counters, truncation accounting, `max_*` bounds, the uniform-overlap
requirement, byte-exact canonical output for v1 inputs, and the three-language equivalence
contract. v2 must pass the existing 39 cases and the 134-workload equivalence unchanged.

## 8. Implementation plan, only after approval (TDD)

1. Spec v2.0 and schema v2.0 text, with a `DECISION_LOG.md` entry approved by Ali.
2. New fixtures (never editing the 39 existing ones), each with hand-derived expectations:
   - node present but edge absent;
   - edge supported in one sample only;
   - every edge supported in some sample but no single sample on all edges;
   - same-sample complete path;
   - different-sample node support;
   - a cross-sample path combination;
   - colour change along a unitig (adapter split);
   - orientation (`−` strand ORF);
   - `strict_edge` without `--edge-support` must be a usage error.
3. Oracle extended first. Then Python, C++ and Rust (RED → GREEN), the timing contract, and
   cross-language equivalence on v1 and v2 workloads.
4. Adapter tests (unitig splitting, oriented doubling, junction (k+1)-mer evidence) live in the
   adapter layer, not in the engine.
