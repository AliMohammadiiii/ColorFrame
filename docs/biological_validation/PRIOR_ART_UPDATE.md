# Prior-Art Update for Biological Validation

**Status:** 2026-11-15. It extends `docs/LITERATURE_REVIEW.md` and
`docs/PRIOR_ART_AND_SCOPE.md`; it does not replace them.

## Method and tool access (stated plainly)

- **Elicit:** used by Ali before this session. The report "Public datasets for biological
  validation of ColorFrame" screened 50 records and extracted 15. It is treated as a discovery
  and extraction aid; every dataset claim used here was re-checked at a primary source.
  No Elicit tool was connected in this session.
- **Scite:** not connected. **No Scite citation-context analysis was performed.** No supporting
  or contrasting citation statements are claimed.
- **Scholar Gateway:** returned `ACCESS_DENIED`.
- **Consensus:** used for one supplementary discovery query about single-cell MDA datasets. Its
  results are leads, verified at accession level only where stated.
- **Primary sources** (all metadata only, 2026-11-15): NCBI E-utilities (BioProject, BioSample,
  Assembly, SRA), ENA Portal API, Europe PMC full text, GitHub repositories (read-only), Zenodo,
  and the CAMI data portal. Raw evidence files are listed in `evidence/README.md`.

## 1. Graph-based gene finding

**ggCaller** (Horsfield et al. 2023, Genome Res, doi 10.1101/gr.277733.123; analyses used
v1.3.4):
- It already does what ColorFrame's v2 proposal points towards: DFS ORF discovery on a Bifrost
  coloured DBG, with FM-index validation of walks against the input sequences.
- Current release: v1.5.2 (MIT, canonical repo `bacpop/ggCaller`). v1.5.0 removed Panaroo
  clustering and made GFF-only output the default, so results from the paper's version and the
  current version must not be mixed.
- It uses ATG/GTG/TTG starts and outputs one GFF per input genome (colour).
- Its manuscript repository (MIT; Zenodo 10.5281/zenodo.8054555, CC-BY-4.0) contains a
  **contig-break benchmark** with ground truth (`all_CDS.fasta`):
  - 5 curated *S. pneumoniae* capsule operons, CR931662.1–CR931666.1, 19–23 kb each,
    16–23 genes each;
  - one random break inserted in each CDS.

  It is the smallest ready-made gene-truth set for fragmentation behaviour.
- Its simulated pangenomes (7 × 100 genomes from *S. pneumoniae* ATCC 700669) are **not stored**;
  they must be regenerated with the authors' script.

ColorFrame's differences, restated:
- no start scoring or orthologue clustering;
- ATG starts only;
- explicit truncation accounting;
- a fully specified traversal with three byte-equivalent implementations;
- and, once v2 is approved, explicit evidence levels L1–L4 reported per sample instead of a
  single validity filter.

## 2. Coloured de Bruijn graph representation: Bifrost (verified from code)

Bifrost v1.3.9 (2026-08-11, BSD-2-Clause; Bioconda lags at 1.3.5). Holley & Melsted 2020,
Genome Biol, doi 10.1186/s13059-020-02135-8.

- **Colours are per k-mer position, not per unitig.**
  - Paper: a unitig with η = |u| − k + 1 k-mers has an η × |C| bit matrix.
  - Code: `UnitigColors` iterates (k-mer position, colour) pairs, with bit index
    `colour_id × nb_kmers + pos` (`src/ColorSet.hpp`).

  So colours can change along one unitig, and the union over a unitig would invent support. This
  confirms the need for the unitig splitting in `GRAPH_SCHEMA_V2_PROPOSAL.md` §5.
- **Colours carry no strand.** Canonical k-mers are coloured, and positions refer to the unitig's
  stored orientation (`ColoredCDBG.tcc`).
- **The graph is bidirected over canonical k-mers.** Edges are not stored; they are found by
  neighbour lookup with strand.
- **GFA export:** `S` lines hold each unitig in its stored orientation, and `L A ± B ± (k−1)M`
  lines hold edges. **Colours are not exported to GFA**; they are in the binary
  `.color.bfg` file. Each edge probably appears in both orientations (inferred from code, not
  run). The adapter must therefore read colours through Bifrost's API or its query mode, not
  from the GFA.

## 3. Linear-genome baseline

**Pyrodigal** v3.7.1 (GPL-3.0-or-later), the same results as Prodigal v2.6.3:
- single-genome and metagenome (`meta=True`) modes;
- ATG/GTG/TTG starts plus edge (partial) genes;
- GFF and FASTA output.

A fair comparison with ColorFrame is possible only on the **eligible subset** (forward-oriented,
ATG, complete, in-range CDSs), and only after mapping both outputs to the same reference
coordinates.

## 4. Simulated multi-sample truth

- **CAMISIM** (Apache-2.0; v2.0.1, 2026-03-23, a Nextflow rewrite; the paper describes the
  Python v1.x). Per sample it writes:
  - reads;
  - per-genome BAMs;
  - `reads_mapping.tsv` (the source genome of every read);
  - a gold-standard assembly with contig → genome coordinates.

  It writes **no gene annotations**. Gene truth must come from the source genomes' annotations.
- **CAMI II Toy Human Microbiome Project** (DOI 10.4126/FRL01-006425518): 49 simulated samples
  across 5 body sites, 2×150 bp at 5 Gbp per sample. Every sample has:
  - abundances;
  - a gold-standard assembly with a mapping file;
  - read provenance.

  Source genomes are RefSeq complete genomes (2017), so NCBI annotations exist. Its gold
  standards are assembly, binning and profiling truth, **not gene truth**. The licence is
  **not verified**.

## 5. AMR benchmark

Raphenya et al. 2022 (Sci Data, doi 10.1038/s41597-022-01463-7; Zenodo, CC-BY-4.0):
- 174 genomes. The paper says 22 species, but Table 1 has 21 organism rows, so the count is
  partially verified.
- The truth is **tool-defined**: RGI v5.2.0 with CARD v3.1.4. It is AMR genes only, not all CDSs.
- The metagenome is a single simulated sample.
- Zenodo record numbers are inconsistent between the paper, the README and the download script.

## 6. Single-cell amplification artefacts

MDA produces uneven coverage and **physical chimeras**, i.e. joins of non-contiguous genomic
regions within one amplified molecule. This is reported e.g. by Rodrigue et al. 2009 and
Nishikawa et al. 2015, found via Consensus at abstract level.

**Consequence for ColorFrame:** in single-cell data, a "chimeric" path can be a real molecule of
that cell's amplified DNA rather than a graph artefact. `POTENTIAL_CHIMERIC_PATH` must therefore
be decided against an **unamplified, same-stock reference**, never against the cell's own
assembly (`VALIDATION_LIMITATIONS.md`).

Datasets with matched bulk material, all verified at ENA/SRA:
- de Bourcy et al. 2014, PRJNA263631, 42 runs: 1 unamplified bulk library, bulk amplification
  dilutions, and 17 distinct single cells (MDA, MALBAC, PicoPLEX);
- Gole et al. 2013, PRJNA209527, K-12 MG1655 single cells;
- Nishikawa et al. 2015, DRA003579.

## 7. Positioning after this update

ColorFrame remains a controlled algorithmic prototype. Its proposed contribution to biological
validation is **methodological**: making node, edge, full-path and CDS evidence separate,
per-sample and auditable. It does not claim better gene finding. No biological-validation claim
is made until the pilot in `BIOLOGICAL_VALIDATION_DECISION.md` has run.
