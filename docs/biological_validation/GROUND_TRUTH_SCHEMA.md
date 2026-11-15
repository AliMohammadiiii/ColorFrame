# Ground-Truth Schema

**Status:** Proposal for review, 2026-11-15. It defines how samples, colours, references,
annotations and provenance are represented. All tables are TSV/CSV with a header; ids are ASCII
without whitespace. Large data never enters Git; the tables reference it by accession, path and
SHA-256.

## 1. Identity: concepts that must never be merged

| Field | Meaning | Example |
|---|---|---|
| `sample_id` | one biological sample: an isolate culture, one single cell, one community aliquot | `ECOR01` |
| `organism_id` | taxon (NCBI TaxID) | `562` |
| `strain_id` | strain designation from the source | `ECOR 1` |
| `library_id` | one sequencing library from a sample | `SAMN…/lib1` |
| `run_id` | one sequencing run (SRA/ENA run) | `SRR…` |
| `sequencing_platform` | instrument platform and model | `ILLUMINA HiSeq 2000` |
| `color_id` | integer graph colour, assigned **only** to a `sample_id` with defensible provenance | `0` |

**Colour rule.** One colour = one `sample_id`. Several libraries and runs of the same sample
(other platforms, replicates) map to the same colour, or are kept out of the graph and used as
independent evidence. A mixed-community library is **one** sample and gets one colour, however
many species it contains.

Splitting a community into per-species colours by read classification is allowed only as a
separately labelled experiment, with `provenance = derived_classification`, and with the
circularity recorded when the classifier used the evaluation references. It is never presented
as observed sample provenance.

## 2. Tables

### `SAMPLE_MANIFEST.csv`: one row per library and run actually used

`sample_id, organism_id, organism_name, strain_id, library_id, run_id, sequencing_platform,
read_type, read_length, bases, reference_accession, reference_completeness, assembly_accession,
annotation_file, color_id, evidence_provenance, verification_status`

- `read_type`: `short_paired`, `short_single`, `long_hifi`, `long_ont`, `long_clr`, `none` (assembly-only).
- `reference_completeness`: `complete` (closed chromosome and plasmids), `draft` (contigs), `none`.
- `evidence_provenance`:
  - `isolate_library` (separately sequenced isolate);
  - `single_cell` (one amplified cell);
  - `mixed_community`;
  - `simulated` (simulator knows the source genome of every read);
  - `derived_classification` (see §1).
- `verification_status`: `Verified`, `Partially verified`, `Not verified`, `Unclear`.

### `references.tsv`

`reference_id, sample_id, accession, version, completeness, n_contigs, total_length,
source_url, sha256, retrieved_utc`

A reference belongs to a sample only if it was produced from that sample (same isolate or
strain). A closely related type-strain genome is recorded as `proxy_for = <sample_id>` and is
never used for L3-ref or chimera decisions.

### `annotations.tsv`: one row per CDS feature

`cds_id, reference_id, contig, start, end, strand, start_codon, stop_codon, length_nt, partial,
pseudo, translation_matches, eligible, exclusion_reason, annotation_source, annotation_version`

Coordinates are 1-based inclusive. `annotation_source` records which annotation was used (for
example `NCBI PGAP 6.x` or the authors' GFF3). Annotations from a gene caller are
**predictions**: they are recorded as such and never presented as experimental truth.

### `candidate_evidence.tsv`: produced by the evaluator

`graph_id, policy, path, start_offset, sequence_sha1, sample_id, L1, L2, L3_ref, L3_asm,
L3_read, L4, label, evidence_ref`

## 3. Provenance file per dataset build

`provenance.json` contains:
- the dataset id and every input accession with its SHA-256;
- tool versions (Bifrost, aligners, Pyrodigal/ggCaller if used), k, filtering parameters;
- the colour assignment table;
- the adapter commit hash and timestamps.

A build without a complete provenance file is not used for any reported result.

## 4. CDS eligibility under current ColorFrame assumptions

A CDS is **eligible** iff all of the following hold. Checks run in the order pseudo, partial,
strand, alt_start, no_canonical_stop, internal_stop, length; the first failing check is the
recorded reason (`adapters/cds.py`):

| # | Condition | `exclusion_reason` if not |
|---|---|---|
| 1 | on the strand the graph represents (v1: the reference's forward strand only; v2 with oriented doubling: both strands) | `strand` |
| 2 | starts with `ATG` | `alt_start` (GTG/TTG/other) |
| 3 | ends with TAA/TAG/TGA and the length is a multiple of 3 | `no_canonical_stop` |
| 4 | not partial and not pseudo | `partial`, `pseudo` |
| 5 | length within `[min_orf_nt, max_orf_nt]` of the run | `length` |
| 6 | no internal in-frame stop (the translation is valid) | `internal_stop` |

Every report states:
1. the total number of annotated CDSs;
2. the number eligible;
3. exclusions by strand, alternative start, partial/pseudo, length and other reasons, which must
   sum to the total.

Recall is computed **only** over eligible CDSs (`PATH_LEVEL_EVIDENCE_PROTOCOL.md` §6).
