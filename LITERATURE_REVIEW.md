# Literature Review

**Status:** Validated for v1.0.1 (2026-11-15). Supersedes the v1.0.0 review, which marked the
ggCaller method details UNVERIFIED.

## Method and tool access

- **Metadata:** every entry in `references.bib` was checked against an authoritative record:
  Crossref (most DOIs), DataCite plus the JUCS landing page (Stein & Geyer-Schulz), or the arXiv
  API (preprints).
- **Full text:** ggCaller was read in full via the Europe PMC full-text API (PMC10620059),
  including the workflow figure legend and the methods.
- **Not available:** Elicit and Scite were **not** available in this session (no connected
  tools), so no Elicit extraction or Scite Smart Citation analysis was performed, and no
  statement here relies on them. The independent review used Elicit; its candidate list was
  re-verified at the primary sources above.
- Only claims supported by the text actually read are made. Papers whose content was not read
  beyond the abstract or metadata are marked as such.

## 1. ggCaller: the closest prior art (full text read)

Horsfield et al. 2023 [`horsfield2023ggcaller`] combine gene prediction, functional annotation and
orthologue clustering in a single population-wide workflow on a Bifrost de Bruijn graph. From the
workflow description (their Fig. 1 and Methods):

1. A coloured DBG is built from assemblies with Bifrost.
2. All stop codons are identified, and the stop-codon frequency is computed.
3. a. Starting from each node with a stop codon, a **depth-first search pairs stop codons with
   downstream stop codons in the same reading frame**.
   b. During the DFS, candidate paths are checked against an **FM-index of the input sequences**,
   removing paths not supported by contiguous input sequence. The paper motivates this with
   "short-circuits" in the DBG.
4. Start codons within stop-to-stop regions are scored by translation-initiation-site sequence,
   **genome coverage given by the number of colours shared in a node**, and how often that start
   is chosen in other potential orthologues.
5. ORFs are clustered into COGs.
6. Balrog scores each cluster's centre sequence.
7. The highest-scoring ORFs are kept, and the clusters are annotated.

**Consequence for ColorFrame:** frame-aware DFS for ORF discovery on a coloured DBG, and the use of
colour sharing as evidence, are established practice. ggCaller's FM-index step addresses
precisely the weakness ColorFrame documents in `LIMITATIONS.md`: a walk through the graph,
even one with shared colours, need not exist contiguously in any input.

## 2. Coloured de Bruijn graphs and scale

- **Iqbal et al. 2012** [`iqbal2012cortex`]: coloured DBGs for assembly and genotyping across
  samples. This is the origin of per-node colour sets.
- **Holley & Melsted 2020** [`holley2020bifrost`]: Bifrost, compacted coloured DBG construction
  and querying. Unitigs overlap by `k − 1`, which motivated ColorFrame's uniform overlap `K`.
- **Karasikov et al. 2025** [`karasikov2025metagraph`]: annotated DBG indexing at very large
  scale. ColorFrame's graphs (≤ 10 000 nodes) say nothing about that scale.

## 3. Making the reading frame explicit

- **Peng, Ji & Zhao 2016** [`peng2016codondbg`] build a codon-based DBG from reads, putting the
  frame into the graph itself. ColorFrame instead keeps the frame in the traversal state.
- **Jaromczyk, Moore & Schardl 2012** [`jaromczyk2012orf`]: a linear-time maximum-length ORF in a
  splice graph. That is an acyclic setting with a single optimum, versus ColorFrame's cyclic
  graphs and enumeration of every candidate. Abstract-level reading only.
- **Kalatzis 2026** [`kalatzis2026tipe`]: bounded path construction in genome graphs. Metadata
  verified via Crossref (IEEE Access 14, 108558–108570), which settles the DOI inconsistency
  raised by the review. **The content was not read**, so no comparison is claimed beyond
  "adjacent work on bounded path construction".

## 4. Per-genome gene finding

Prodigal [`hyatt2010prodigal`], FragGeneScan [`rho2010fraggenescan`] (partial and frameshifted
genes in short reads) and Balrog [`sommer2021balrog`] (universal protein model) are the per-genome
callers and scorers that ggCaller builds on or compares against. They are cited for context
only; ColorFrame scores nothing.

## 5. Benchmarking methodology

- **Stein & Geyer-Schulz 2013** [`stein2013languages`]: a controlled comparison of five
  programming-language implementations of one graph task (runtime and memory). It is the closest
  methodological precedent for RQ2.
- **Beamer, Asanović & Patterson 2015** [`beamer2015gap`]: the GAP suite, with specifications,
  workloads, reference outputs and methodology. ColorFrame follows the same pattern of shared
  specification, reference outputs and verification before timing.
- **Mehrotra et al. 2024** [`mehrotra2024sok`] warn that synthetic graph generators and vertex
  ordering can distort graph-benchmark conclusions. ColorFrame's graphs are synthetic and its ids
  are sorted (which fixes traversal and memory order). Its timing results are therefore specific
  to these workloads (`LIMITATIONS.md`).

## 6. AI-assisted software development

- **Peng et al. 2023** [`peng2023copilot`]: a controlled experiment in which developers with
  GitHub Copilot completed a task faster.
- **Becker et al. 2025** [`becker2025metr`]: a randomised study in which experienced open-source
  developers took *longer* with early-2025 AI tools.

Read at abstract level, these results point in opposite directions. That supports treating
ColorFrame's AI-usage data as a descriptive process trace, not as evidence about AI efficiency.
ColorFrame's own process evidence (tests catching fixture errors, review catching measurement
errors) is consistent with the common lesson that agent output needs tests, review and
traceability.

## 7. Position of ColorFrame

ColorFrame is a **controlled algorithmic and engineering prototype** inspired by the
graph-traversal and evidence-support questions of single-cell microbial genomics. It is not a
gene caller, and it claims no novelty for ORF discovery, frame-aware traversal, colour support or
bounded path search. See `PRIOR_ART_AND_SCOPE.md` for the point-by-point comparison with ggCaller.
