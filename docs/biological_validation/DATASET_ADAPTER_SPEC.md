# Dataset Adapter Specification

**Status:** Proposal for review, 2026-11-15. Adapters turn public dataset records into
ColorFrame inputs plus the ground-truth tables. They live outside the ColorFrame core (a new
`adapters/` package, Python standard library plus external tools invoked as subprocesses). No
adapter code is written before the design is approved.

## 1. Pipeline

```
DATASET_MANIFEST row
  └─ 1. resolve   accessions → exact file list (ENA/NCBI metadata), sizes, MD5
  └─ 2. fetch     only listed files → data store (Modal Volume), verify MD5, record SHA-256
  └─ 3. samples   SAMPLE_MANIFEST rows; colour assignment (GROUND_TRUTH_SCHEMA §1)
  └─ 4. truth     references.tsv, annotations.tsv (+ eligibility)
  └─ 5. graph     Bifrost build (one input file per colour) → GFA + colour query
  └─ 6. split     unitigs split at colour-change boundaries  (v2 proposal §5)
  └─ 7. orient    oriented doubling u+/u−                     (v2 proposal §6)
  └─ 8. emit      nodes.tsv, edges.tsv (+ edge_support.tsv if v2 approved), provenance.json
  └─ 9. evaluate  ColorFrame run → candidate_evidence.tsv     (PATH_LEVEL_EVIDENCE_PROTOCOL)
```

Stages 1–8 are timed and logged separately (`prep_*_s`). They are never added to ColorFrame's
`total_ms`.

## 2. Inputs per evidence type

| Source | Graph input | Evidence use |
|---|---|---|
| complete isolate reference | Bifrost `-r` (reference mode: every k-mer kept) | L1 colours, L2 junctions, L3-ref, L4 |
| isolate assembly (draft) | `-r` | L1, L2, L3-asm (`partial` at contig ends) |
| isolate reads (short) | `-s` (sequencing mode, k-mer abundance filter) | L1, L2 via junction (k+1)-mers |
| long reads (HiFi/ONT) | not used to build the graph (default) | L3-read only |
| single-cell assembly (SAG) | `-r` | L1, L2, L3-asm (sample-specific) |
| simulator output | per-sample reads `-s` or genomes `-r` | L1–L4 with simulator provenance |

Same-sample independence: when a sample's reference is used both to **build** the graph and to
**evaluate** L3, then L3-ref for that sample is a consistency check of the adapter, not
independent evidence. The headline evaluation therefore builds graphs from **reads or
assemblies** and evaluates against **references**, wherever the dataset allows it.

## 3. Graph-size control

ColorFrame v1 is tested up to 10,000 nodes. A bacterial multi-sample DBG has 10⁵–10⁶ unitigs.
Two modes:

- **Locus windows (pilot default).** Choose N loci: eligible CDSs plus negative-control
  intergenic regions, sampled deterministically with a recorded seed. Keep the unitigs that
  contain k-mers of `locus ± flank` in any sample, plus neighbours up to radius `r`. Emit one
  `graph_id` per locus. Bounded, reproducible, and every candidate stays attributable to a known
  locus.
- **Whole graph.** Allowed only after a pilot measures states/s and memory on the target data
  (compiled implementations only; Python is too slow at this scale). Requires Ali's approval
  if Modal cost is material.

## 4. Determinism and ids

- Node ids: `u<unitig_index>s<segment>±`, stable for a given Bifrost version, k and input order.
  Inputs are sorted by `sample_id`, and the colour order equals the sorted `sample_id` order.
- Every emitted file has a SHA-256 in `provenance.json`. Re-running an adapter on the same
  inputs must reproduce byte-identical outputs (an adapter test).

## 5. Per-dataset adapters (each with its own tests)

| Adapter | Colours | Notes |
|---|---|---|
| `isolate_collection` (e.g. ECOR, Zymo isolates) | one per isolate library | references or assemblies per isolate |
| `mixed_community` (MBARC-26, BMock12, Zymo community) | **one** per community library | species references used only for L3/L4, never as colours |
| `camisim` | one per simulated sample | provenance from the simulator's read-to-genome mapping |
| `single_cell_sag` (GORG-Dark subset, SPAdes ECOLI-SC) | one per SAG/cell | no complete per-cell reference; L3-asm only; no gene-level P/R |

## 6. Adapter tests (TDD, before code)

1. Resolve: a pinned metadata snapshot gives the exact file list.
2. MD5 mismatch aborts.
3. A mixed-community library yields exactly one colour.
4. A unitig with a colour change splits into two nodes with overlap `k−1`, each with exact colours.
5. Oriented doubling: a `−` strand ORF is found once, with its correct reference coordinates.
6. A junction (k+1)-mer yields edge evidence in the right sample only.
7. Locus-window extraction is deterministic for a given seed.
8. The provenance file is complete.
9. Byte-identical re-run.
10. Missing reference or annotation produces an explicit `none` status, never a silent drop.
