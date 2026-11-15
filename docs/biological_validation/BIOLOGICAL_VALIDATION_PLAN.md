# Biological Validation Plan

**Research direction: Ali Mohammadi.** The ideas originate with him:
- moving beyond synthetic fixtures;
- using sample-resolved evidence;
- separating node support from complete-path validity;
- detecting chimeric paths created by branching and cross-sample pooling;
- combining isolates, controlled simulation and single-cell data;
- comparing strict and permissive policies.

This plan, written by the coordinating development agent (Claude Opus 5.5), translates that
direction into a validation programme. **Status:** Phase 1–3 feasibility package, 2026-11-15,
awaiting Ali's approval. Nothing has been downloaded, and the ColorFrame engine is unchanged.

## 1. Motivation

On synthetic graphs, ColorFrame's three implementations agree byte for byte, and RQ1 showed how
the strict and permissive policies behave under controlled noise. Synthetic correctness says
nothing about biology. The question now is whether the evidence behind a graph path corresponds
to a real, sample-consistent sequence. ColorFrame should separate five situations:

1. a coding sequence supported by one sample;
2. nodes present in samples, but the full path absent;
3. a path assembled from segments of different samples;
4. a real coding path that is hard to recover (fragmentation, sparse coverage);
5. insufficient evidence.

## 2. Evidence model

Four non-interchangeable levels: node (L1), edge (L2), full path (L3), annotated CDS (L4). There
are ten candidate labels with explicit rules. A chimera is claimed only on confirmed
contradiction. See `PATH_LEVEL_EVIDENCE_PROTOCOL.md`; the identities, colours and truth tables
are in `GROUND_TRUTH_SCHEMA.md`.

## 3. Selection criteria

Every dataset was scored on three independent dimensions, all verified at primary sources:
- (A) sample-resolved evidence;
- (B) gene-level ground truth;
- (C) path-level evidence.

Publication prestige and dataset size were not criteria. The full matrix is in
`DATASET_FEASIBILITY_MATRIX.csv`.

## 4. Tiers and selection

| Tier | Dataset | A | B | C | Role |
|---|---|---|---|---|---|
| Primary real-isolate | **ECOR** (72 *E. coli* isolates; Illumina per isolate + independent complete ONT genomes) | yes | yes | yes | main benchmark |
| Primary controlled | **CAMISIM from ECOR complete genomes** | by construction | yes | exact | secondary: designed cross-sample overlap, depth sweeps |
| Single-cell stress | **de Bourcy 2014** (17 *E. coli* cells + unamplified bulk library) | yes | via same-stock bulk | partial | optional |
| Mock-community validation | Zymo D6300 | yes (isolates) | yes (8 bacteria) | yes | next tier, deferred |
| Platform-specific | BMock12, HiFi MSA-1003 | no | partial/yes | references only | deferred |
| Community-level | MBARC-26 | no | yes | references only | deferred |
| Single-cell at scale | GORG-Dark | yes | no | weak | deferred |
| Prior-art | ggCaller contig-break operons | n/a | yes | yes | fragmentation sanity check |
| Excluded | SPAdes ECOLI-SC (reads not deposited); FASTQSim (not investigated); Nishikawa 2015 (unclear run structure) | | | | |

## 5. Phases

0. Audit of the existing project. Done: v1.0.1 is preserved, and this work is on
   `feat/biological-validation`.
1. Literature and dataset audit. Done (this package).
2. Scientific feasibility: graph-model audit and minimal extension. Done as a proposal
   (`GRAPH_SCHEMA_V2_PROPOSAL.md`).
3. Selection. **Awaiting Ali** (`BIOLOGICAL_VALIDATION_DECISION.md`).
4. Pilot of about 1.86 GB (`DOWNLOAD_PLAN.md`), after approval:
   - identity gates;
   - locus-window graphs from ECOR Illumina reads;
   - L1–L4 evaluation against the complete genomes;
   - a 3-sample CAMISIM run;
   - de Bourcy coverage and chimera behaviour.
5. Graph model and adapters: test-first, only what the pilot shows to be needed.
6. Full validation runs.
7. Reporting: R figures, a reproducibility package, and updated limitations and literature.

## 6. Ground-truth methodology (summary)

- Graphs are built from **reads** (or draft assemblies) and evaluated against **independent
  complete references** and their annotations.
- References are never used to build the graph that they evaluate, except as a labelled adapter
  consistency check.
- Gene metrics use only the eligible CDS subset, with exclusion counts.
- Preparation and graph construction are timed separately from ColorFrame traversal.

## 7. Limitations

See `VALIDATION_LIMITATIONS.md`.
