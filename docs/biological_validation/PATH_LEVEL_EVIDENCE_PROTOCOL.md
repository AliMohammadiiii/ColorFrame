# Path-Level Evidence Protocol

**Status:** Proposal for review, 2026-11-15. It defines how every ColorFrame candidate is
evaluated against every relevant sample. It is applied **after** the search, by the evaluation
layer; it does not change the search.

## 1. Inputs

- A ColorFrame candidate: `graph_id, policy, path` (oriented node ids), `start_offset`, spelled
  `sequence` (ATG … stop), node colour sets, and edge evidence if available (schema v2).
- The sample manifest (`SAMPLE_MANIFEST.csv`): for each `sample_id`, any of
  - a complete reference (closed genome), recorded with its completeness;
  - a sample-specific assembly, recorded with its contig count;
  - reads, recorded with platform and read length.
- The annotation set (`GROUND_TRUTH_SCHEMA.md`): CDS features with an `eligible` flag.

## 2. Evidence levels (never interchangeable)

| Level | Name | Definition for candidate `c` and sample `s` |
|---|---|---|
| L1 | node support | every node of `c` carries colour `s` (k-mer exact after unitig splitting) |
| L2 | edge support | every traversed edge of `c` is observed in `s` (junction (k+1)-mer present in `s`'s evidence source) |
| L3 | full-path support | the complete spelled sequence of `c` occurs contiguously in `s` (§3) |
| L4 | annotated CDS support | `c` matches an eligible annotated CDS of `s`'s reference (§4) |

Implications only run one way: L3 ⇒ L2 ⇒ L1, when all three are computed from the same
sample's sequences. Nothing implies L3 except an L3 test, and L4 additionally requires an
annotation.

## 3. L3: full-path tests

All tests search **both strands**, require 100% sequence identity over the full length (the
spelled sequence comes from sample-derived graph sequence, so mismatches mean another sequence),
and record `sample_id, source, contig, start, end, strand, identity, aligned_fraction`.

| Test | Source | Result values |
|---|---|---|
| L3-ref | complete sample reference | `complete` (exact full-length match) / `absent` |
| L3-asm | sample assembly | `complete` / `partial` (a prefix or suffix ≥ 50% ends at a contig end: an assembly break) / `absent` |
| L3-read | long reads (HiFi/ONT) | `molecule` (≥ 1 read spans the full sequence at ≥ 99% identity for HiFi; for ONT a consensus of ≥ 3 spanning reads) / `junctions_only` (every junction covered by some read, none spans all) / `none` |

For short reads, L3-read is limited to `junctions_only`, or consecutive junctions within one read
or pair. Separate junction coverage never establishes a molecule (Principle 2).

Exact search: two-strand substring search (Aho–Corasick or an FM-index over the sample's
sequences). The ggCaller FM-index check is the precedent.

## 4. L4: annotated CDS test

Candidate `c` in sample `s` matches CDS `g` of `s`'s reference when:
- **strand**: the same as the CDS;
- **stop**: identical stop coordinate (the 3′ end must match exactly);
- **start**:
  - `exact`: identical start;
  - `upstream` or `downstream`: a different in-frame ATG, with Δ recorded in codons;
- **translation**: matches the annotation's `/translation` where present;
- **eligibility**: `g` is eligible (`GROUND_TRUTH_SCHEMA.md` §4).

Reported as `exact_match`, `boundary_shift(Δ)` or `no_match`. Gene-level precision and recall
use only eligible CDSs (§6).

## 5. Classification (one label per candidate, first rule that applies)

Let `S(c)` be the samples with L1 support, and `R` the samples that have a **complete** reference.

| # | Label | Rule |
|---|---|---|
| 1 | `ANNOTATED_CDS_MATCH` | L4 `exact_match` in some sample (record which) |
| 2 | `FULL_REFERENCE_PATH` | L3-ref `complete` in some sample, not rule 1 |
| 3 | `FULL_ASSEMBLY_PATH` | L3-asm `complete`, or L3-read `molecule`, in some sample; not rules 1–2 |
| 4 | `POTENTIAL_CHIMERIC_PATH` | **confirmed contradiction**: every sample in `S(c)` is in `R`, L3-ref is `absent` in all of them, and the path splits into ≥ 2 consecutive segments that each occur contiguously in some sample's complete reference |
| 5 | `CROSS_SAMPLE_INCONSISTENT` | L1 holds only with different samples on different nodes (no single sample in all), and rule 4's completeness conditions are not met |
| 6 | `EDGE_SUPPORTED_ONLY` | some sample has L2 on all edges, but no sample has L3 `complete` or `molecule` evidence (and rule 4 did not apply) |
| 7 | `FRAGMENTED_PATH_EVIDENCE` | L3-asm `partial` (assembly break) or L3-read `junctions_only` in some sample |
| 8 | `NODE_SUPPORTED_ONLY` | some sample has L1 on all nodes; L2 not tracked or not complete; no L3 |
| 9 | `UNRESOLVED` | evidence exists but conflicts or is ambiguous (e.g. multi-mapping, palindromic nodes) |
| 10 | `UNSUPPORTED` | no sample has L1 on all nodes (possible only under `permissive`, or with uncoloured nodes) |

**The chimera rule is deliberately strict.** A path absent from an *incomplete* assembly, or from
a sample without a complete reference, is never labelled chimeric. It falls to rules 5–9.
Missing evidence is reported as missing (Principles 5 and 8).

Every label is stored with the evidence that triggered it (sample, source, coordinates), so any
label can be re-derived.

## 6. Metrics

**Gene level**, eligible CDS subset only:
- `TP` = eligible CDSs with an `exact_match` candidate;
- `FP` = candidates on samples with a complete reference that match no eligible CDS **and** are
  not `FULL_REFERENCE_PATH` non-CDS ORFs. These "real but unannotated ORFs" are counted
  separately and never as false genes;
- precision, recall, F1, exact-boundary rate, shifted-boundary rate, and the candidate length
  distribution.

**Path level** (rate = label count ÷ candidates, per dataset and per policy): every label in §5.

**Evidence support**: strict and permissive recovery, true shared and local support, spurious
shared and local support (RQ1 definitions), and the ambiguity rate.

**Performance**: existing ColorFrame metrics, unchanged. Data preparation, graph construction
and evaluation are timed separately and never added to traversal time.

## 7. Required tests (evaluation layer)

Node present but edge absent · edge supported in one sample only · all edges supported but no
full reference path · same-sample complete path · different-sample node support · cross-sample
combination · unitig colour variation · reverse-strand candidate · partial assembly (break at a
contig end) · missing reference · missing annotation · ambiguous mapping (multi-hit).

Each test has a hand-derived expected label and evidence record.
