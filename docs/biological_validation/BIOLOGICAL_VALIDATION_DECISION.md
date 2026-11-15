# Biological Validation — Decision Memo (for Ali's approval)

2026-11-15 · prepared by the coordinating agent (Claude Opus 5.5). The research direction and
the final decisions are Ali's. Every fact below was verified at NCBI, ENA, Europe PMC, GitHub or
Zenodo, or is explicitly marked otherwise. **Nothing has been downloaded or validated yet.**

## Which dataset first?

**ECOR**, the *E. coli* reference collection: 4 isolates in the pilot.

**Why:**
- It is the only candidate that meets all three requirements with **independent** evidence.
- Each of the 72 isolates has its own Illumina library from US FDA project PRJNA230969. Each
  library is a genuine sample, so each isolate is a defensible colour.
- Each also has a **complete** genome from a different project, PRJNA1543032 (ONT, released
  2026-11-10), with RefSeq/PGAP annotation.
- So the graph is built from one lab's reads and judged against another project's closed genomes.
- Being one species, it gives shared and accessory sequence across samples. That is exactly what
  creates cross-sample paths and potential chimeras.

Two corrections to the earlier notes:
- PRJNA230969 is a broad FDA *E. coli* project (1,705 BioSamples), not "the ECOR project". The 72
  ECOR isolates are part of it.
- The complete genomes are a new resource not mentioned in the notes.

## Which offers the strongest path-level truth?

- **Real data: ECOR.** Closed per-isolate chromosomes and plasmids, so an exact full-length
  search decides L3 for each sample.
- **By construction: the CAMISIM simulation from the ECOR genomes** (secondary). CAMISIM records
  the source genome of every read, and the overlap between samples is designed. For example:
  - S1 = {ECOR01, ECOR56}
  - S2 = {ECOR56, ECOR69}
  - S3 = {ECOR69, ECOR72}

  Each simulated sample is one colour.

  The CAMI II toy HMP was considered and deferred: its urogenital samples share at most 6 of 24
  genomes (verified), and its licence could not be verified.

## Which is the strongest real single-cell stress test?

**de Bourcy et al. 2014** (PRJNA263631):
- 17 single *E. coli* cells amplified by MDA, MALBAC or PicoPLEX;
- an **unamplified bulk library from the same stock**, which provides a same-stock reference.

The pilot uses the bulk library and 3 MDA cells.

GORG-Dark (9,698 SAGs) has no references, so it allows no gene-level metric; it is deferred.
ECOLI-SC from SPAdes is not deposited in SRA or ENA.

## Exact files and size

Total about 1.86 GB; exact URLs and MD5s are in `DOWNLOAD_PLAN.md`.
- **ECOR reads:** SRR3989531, SRR7819142, SRR3989539, SRR7819146. 905,242,623 bytes.
- **ECOR references:** complete genomes and annotation GCF_062083226.1, GCF_062082974.1,
  GCF_062082961.1, GCF_062082958.1 (~12 MB), plus the four FDA draft FASTAs for the identity
  gate.
- **de Bourcy reads:** SRR1613979 (bulk), SRR1614004, SRR1614005, SRR1614006 (MDA cells).
  928,043,766 bytes.
- **DH10B proxy reference:** CP000948.1 (~10 MB).

Nothing else: no raw signal, no full projects.

## What changes to the graph model are necessary?

**For the pilot: none in the search engine.**
- Unitig splitting at colour changes and oriented doubling (both strands) are **adapter**
  transformations that produce valid v1.1 inputs (uniform overlap `k−1`).
- Edge (L2), path (L3) and CDS (L4) evidence are computed **after** the search, by the
  evaluation layer.

**Possibly later:** schema v2 with `edge_support.tsv` and an additive `strict_edge` policy
(`GRAPH_SCHEMA_V2_PROPOSAL.md`). This is worth implementing only if the pilot shows that many
strict (shared-node) candidates fail edge support. It would be decided then, with tests first.

## What can be validated without changing the current algorithm?

- Node-level (L1) strict and permissive behaviour on real graphs.
- Full-path (L3) support for every candidate, per sample, against complete genomes.
- Annotated-CDS (L4) matches and eligible-subset precision and recall.
- Cross-sample inconsistency, and potential chimeras where all supporting samples have complete
  references.
- Fragmentation effects (de Bourcy).
- Edge (L2) evidence as a post-hoc label.

The only thing that needs v2 is **pruning** the search by edge evidence.

## What claims can we legitimately make afterwards?

**If the pilot passes:**
- statements about **these isolates and cells**, at named evidence levels: e.g. "x% of strict
  candidates in 4 ECOR isolates occur contiguously in the supporting isolate's complete genome";
- eligible-subset gene metrics against RefSeq/PGAP annotation.

**Never:**
- "validated genes";
- recall over all CDSs;
- chimera claims from incomplete assemblies;
- per-species colours for mixed communities;
- generalisation beyond *E. coli* or beyond the locus windows tested;
- any novelty claim over ggCaller.

## Decisions requested from Ali

1. Approve ECOR as primary, CAMISIM-from-ECOR as secondary, and de Bourcy as the optional
   single-cell set.
2. Approve the pilot download (≈ 1.86 GB to a Modal Volume) and small Modal runs: CAMISIM,
   Bifrost, evaluation.
3. Confirm the Modal token exposed earlier has been revoked and replaced.
4. Defer schema v2 until the pilot data are in. Alternatively, approve it now so that it is
   implemented test-first.
