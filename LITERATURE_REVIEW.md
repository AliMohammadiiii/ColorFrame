# Literature Review

**Status:** Validated (bibliographic metadata); method summaries limited as marked.

## Method

A supporting agent fetched the Crossref record of every DOI on 2026-11-14 and checked authors,
titles, venues, volumes and pages; `references.bib` contains only those verified entries.
Method summaries below come from the abstracts or publisher/index excerpts that were accessible.
Where the full text could not be accessed (the PMC page was behind a bot check and a fetch hit
an API spend limit), the corresponding statement is marked **UNVERIFIED** and must be checked
against the paper before it is repeated in an interview or report.

## 1. Coloured de Bruijn graphs

- **Iqbal et al. 2012** (Cortex) introduced coloured de Bruijn graphs, in which each k-mer
  carries the set of samples ("colours") it occurs in, for de novo variant assembly and
  genotyping across samples [`iqbal2012cortex`]. ColorFrame borrows only the *idea* of a colour
  set per node; it builds no de Bruijn graph.
- **Holley & Melsted 2020** (Bifrost) build compacted coloured de Bruijn graphs in parallel and
  memory-efficiently, and support indexing, editing and querying [`holley2020bifrost`].
  Compacted unitigs overlap by `k − 1`, which motivated ColorFrame's uniform overlap `K`
  (D-002).
- **Karasikov et al. 2025** (MetaGraph) index very large sequence collections with annotated de
  Bruijn graphs [`karasikov2025metagraph`]. Relevant as the scale end-point: ColorFrame graphs
  are tiny by comparison and make no scalability claims at that level.

## 2. Gene finding on graphs

- **Horsfield et al. 2023** (ggCaller) is a population-wide gene caller that works on de Bruijn
  graphs and combines gene prediction, functional annotation and clustering, reporting speed-ups
  over per-genome pipelines with equal or better accuracy [`horsfield2023ggcaller`].
  An index excerpt says it adapts Panaroo's gene-graph approach to remove spurious clusters and
  re-find genes, and compares against Balrog, Prodigal, Glimmer and GeneMarkS-2.
  **UNVERIFIED** (full text not accessed): exactly how ggCaller traverses its Bifrost graph,
  tracks reading frames and handles stop codons. ColorFrame does not claim to reproduce or
  approximate ggCaller.
- **Peng, Ji & Zhao 2016** (inGAP-CDG) build a *codon-based* de Bruijn graph from predicted
  ORFs in RNA-seq reads, filtering candidates with an SVM; the codon graph is reported to be
  about one third of the size of a nucleotide graph [`peng2016codondbg`]. This is a different
  way to make frame explicit: in the graph itself rather than in the traversal state, as
  ColorFrame does.
- **Jaromczyk, Moore & Schardl 2012** give a linear-time algorithm for the maximum-length ORF
  in a splice graph [`jaromczyk2012orf`] (abstract of the IJCBDD paper **UNVERIFIED**; summary
  from the group's companion abstract). Their dynamic programming exploits the acyclic structure
  of splice graphs. ColorFrame's graphs may contain cycles and it enumerates all candidates
  rather than one optimum, so it uses bounded enumeration instead.

## 3. Gene prediction in fragmented data and clustering

- **Hyatt et al. 2010** (Prodigal): prokaryotic gene recognition and translation-initiation
  site identification [`hyatt2010prodigal`] (abstract **UNVERIFIED**; cited as the standard
  per-genome baseline).
- **Rho, Tang & Ye 2010** (FragGeneScan) combine an HMM with sequencing-error models and codon
  usage to predict genes in short reads, including frameshifted and partial genes
  [`rho2010fraggenescan`]. This is relevant to sparse single-cell data, where most genes are
  partial — something ColorFrame v1 does not report (`LIMITATIONS.md`).
- **Sommer & Salzberg 2021** (Balrog): a single protein model trained across many species, so
  no per-genome retraining is needed [`sommer2021balrog`]. It is a candidate *scorer* that
  could rank ColorFrame's candidates in future work.
- **Tonkin-Hill et al. 2020** (Panaroo): graph-based pangenome clustering that accounts for
  annotation errors such as fragmentation, contamination and misassembly
  [`tonkinhill2020panaroo`].

## 4. What this means for ColorFrame

Graph-based gene prediction, reading-frame tracking and ORF discovery are all established; none
is claimed as new here. ColorFrame's contribution is narrower (see `PRIOR_ART_AND_SCOPE.md`):

1. a fully specified, bounded enumeration with explicit truncation accounting;
2. a controlled comparison of two colour-support policies under simulated per-cell dropout;
3. three byte-equivalent implementations used for an engineering comparison and an AI-assisted
   development case study.
