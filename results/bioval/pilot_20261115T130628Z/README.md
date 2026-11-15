# Pilot stage 1 (data), Modal, 2026-11-15T13:06Z

Volume `colorframe-bioval`, `raw/`. 25/25 pilot files fetched on Modal: reads verified by size
and ENA MD5, NCBI packages by their bundled `md5sum.txt`. SHA-256 for every file is in
`fetch_log.tsv`. Fetch wall time 258 s; minimap2 2.24-r1122.

**Read sanity:** all 8 runs match ENA `base_count` exactly (`read_sanity.tsv`).

**Identity gate** (FDA Illumina draft vs ONT complete genome; minimap2 `asm5`, primary
alignments; thresholds identity ≥ 0.999 and aligned fraction ≥ 0.98):

| Isolate | Identity | Draft aligned | Gate |
|---|---|---|---|
| ECOR01 | 0.99765 | 0.9928 | **FAIL** |
| ECOR56 | 0.99962 | 0.9997 | pass |
| ECOR69 | 0.99942 | 0.9998 | pass |
| ECOR72 | 0.98850 | 0.9999 | **FAIL** |

ECOR72 aligns almost completely but at only 98.85% identity. That pattern fits either
differences between stocks **or** base/indel errors in the ONT-only complete genome. Which one
is not yet known; it matters for every ECOR complete genome used as truth. Next diagnostic:
- break the differences down into mismatches vs indels and homopolymer context;
- map each isolate's own Illumina reads onto its complete genome, to tell assembly errors from
  biological differences.

**CDS eligibility** (complete genome + PGAP GFF; `cds_eligibility_summary.tsv`, per-CDS table
gzipped). At `max_orf_nt` 6000 with both strands searched, 3,868–4,088 of 4,445–4,737
annotated CDSs per isolate are eligible (86–88%). Exclusions:
- 138–200 pseudo;
- 405–437 non-ATG starts;
- ≤ 3 internal stops;
- ≤ 9 over length.

At the default `max_orf_nt` 1200 about 1,000 more per isolate fall out on length, and
forward-strand-only searching would exclude about 2,100–2,200 on strand. So oriented doubling
and a larger `max_orf_nt` are both needed for a meaningful recall.

Note: a first attempt also left `raw/debourcy2014/reference/CP000948.1.fasta` (efetch FASTA) on
the volume. It is superseded by GCF_000019425.1 and not used.
