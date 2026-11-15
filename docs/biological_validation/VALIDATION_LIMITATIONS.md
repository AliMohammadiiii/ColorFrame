# Validation Limitations: what each dataset can and cannot show

**Status:** 2026-11-15. It applies to the proposed biological validation. The v1.0.1 limitations
(`docs/LIMITATIONS.md`) still apply.

## 1. General limits that no dataset removes

1. **Node support ≠ edge support ≠ path support ≠ gene** (`PATH_LEVEL_EVIDENCE_PROTOCOL.md` §2).
   Every result names its evidence level.
2. **Restricted gene model.**
   - ATG starts only. GTG/TTG starts, frameshifts and partial genes are excluded and counted
     (`GROUND_TRUTH_SCHEMA.md` §4).
   - Without oriented doubling, only one strand per node orientation is searched.
   - Recall is reported only over the eligible CDS subset.
3. **Annotations are predictions.** RefSeq/PGAP CDSs are computational annotations, not
   experimental gene truth. A candidate that is a real ORF but unannotated is reported
   separately and never as a "false gene".
4. **Missing evidence is not negative evidence.** A path absent from a draft assembly or a
   single-cell assembly is `UNRESOLVED` or `FRAGMENTED_PATH_EVIDENCE`, never "false".
   `POTENTIAL_CHIMERIC_PATH` requires complete references for every supporting sample.
5. **Graph scale.** ColorFrame is validated up to 10⁴ nodes. The pilot uses locus windows
   (`DATASET_ADAPTER_SPEC.md` §3). Whole-graph results would need a separate performance study.
6. **Graph construction is external.** Bifrost's k, filtering and version change the graph and
   are recorded. Results depend on them.
7. **No ground truth for biological function.** No claim about protein function, expression or
   fitness is made.

## 2. Per dataset

| Dataset | Can show | Cannot show |
|---|---|---|
| **ECOR** (primary) | Per-isolate sample-consistent path support against **independent** complete genomes (Illumina reads from US FDA, ONT complete genomes from another project); gene-level P/R on the eligible subset; cross-isolate chimeric paths in a same-species pangenome | Behaviour on other species; single-cell effects. **Stock caveat:** reads and complete genomes may come from different stocks (4 isolates already disagree in size); a per-isolate identity gate is required. One species only. |
| **CAMISIM from ECOR genomes** (secondary) | Exact truth for which genome produced every read; designed cross-sample overlap; depth and abundance sweeps; mixed samples (several genomes in one colour), so within-sample cross-genome chimeras become visible | Real sequencing error profiles and biases (simulated); anything beyond the input genomes |
| **de Bourcy 2014** (optional single-cell) | Coverage dropout and fragmentation in real MDA/MALBAC/PicoPLEX single cells; behaviour of candidates under amplification artefacts, judged against a same-stock **unamplified** bulk assembly | Multi-strain paths (one strain only); exact reference identity (TOP10 vs DH10B is unclear); independence of the 5 "secondary" MDA libraries. **MDA itself creates physical chimeras**, so a path present in one cell but absent from the bulk reference may be a real amplified molecule, not a graph artefact. |
| Zymo D6300 (deferred) | Isolate-coloured graphs of 8 distinct bacterial species; a real mixed-community library as one extra colour | Same-species pangenome effects; reference-to-isolate identity is only partly verified (strain labels differ) |
| MBARC-26, BMock12, HiFi MSA-1003 (deferred) | Community-level candidates checked against published strain genomes; platform effects (BMock12); molecule-level long-read checks (HiFi) | **Sample-resolved colours**: each is one mixed sample. Per-species colours would be invented provenance. References are not sequenced from the mock material. |
| CAMI II toy HMP (deferred) | Simulated truth at many samples | Cross-sample path tests: verified genome overlap between urogenital samples is low (≤ 6 of 24); licence not verified |
| GORG-Dark (deferred) | Fragmentation and partial-path behaviour in real single-cell assemblies at scale | Gene-level precision or recall (no references; completeness largely unknown) |
| Raphenya AMR (deferred) | A focused AMR-gene subset | General CDS truth (truth is RGI/CARD-defined) |
| ggCaller contig-break set (prior art) | Fragmentation sensitivity on 5 operons with a CDS truth set | Multi-sample or colour behaviour |

## 3. Process limits

- Scite and Elicit were not connected in this session. Scholar Gateway was denied. Literature
  checks used primary sources and one Consensus query.
- The GORG-Dark paper's full text and the CAMI toy HMP licence could not be read (bot
  challenges; not bypassed).
- One verification agent read a 64 KB byte range of a CAMI tarball to list its member names;
  no other data content was retrieved.
