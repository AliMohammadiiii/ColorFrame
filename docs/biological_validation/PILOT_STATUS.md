# Biological-Validation Pilot — Status

**Last updated:** 2026-11-15. Branch `feat/biological-validation`; `main` and tag `v1.0.1` are
unchanged. Decision D-028 approved by Ali: run on Modal, downloads allowed.

| Stage | State | Where |
|---|---|---|
| Feasibility package (12 documents, verified at primary sources) | **Done** | this folder |
| Adapters: verified fetch, CDS eligibility, identity gate, difference classifier | **Done**, test-first (19 tests pass) | `adapters/`, `tests/adapters/` |
| Stage 1 on Modal: download 25 files, read sanity, identity gate, CDS eligibility | **Done** | `results/bioval/pilot_20261115T130628Z/` |
| Identity diagnostic (ONT assembly errors vs stock differences) | **Written, NOT run.** Stopped by Ali before completion; no results exist. | `bioval/modal_diagnose.py` |
| Graph construction (Bifrost), unitig splitting, oriented doubling, locus windows | Not started | `DATASET_ADAPTER_SPEC.md` |
| Evaluation layer (L1–L4 labels) | Not started | `PATH_LEVEL_EVIDENCE_PROTOCOL.md` |
| CAMISIM from ECOR genomes | Not started | — |
| de Bourcy single cells (bulk assembly, coverage, chimeras) | Data downloaded and verified; analysis not started | — |
| Schema v2 (`edge_support.tsv`, `strict_edge`) | Deferred until the pilot data are in | `GRAPH_SCHEMA_V2_PROPOSAL.md` |

## Results so far (stage 1)

- **Data:** all 8 runs match ENA base counts exactly. Every file is MD5-verified, and its
  SHA-256 is recorded.
- **Identity gate:** ECOR56 and ECOR69 pass; ECOR01 and ECOR72 fail. ECOR72 shows 98.85%
  identity at 99.99% alignment between the FDA draft and the ONT complete genome.
- **Open question:** whether that failure is ONT assembly error or a stock difference. It
  matters for every ECOR complete genome used as truth, and it is what the diagnostic answers.
- **CDS eligibility:** 86–88% of annotated CDSs are eligible with both strands and
  `max_orf_nt` 6000. Forward-only search or the default `max_orf_nt` 1200 would exclude far more.

## Next step when resumed

```bash
modal run bioval/modal_diagnose.py
```

It reruns from the data already on the Modal Volume `colorframe-bioval`: no download, about 10
minutes on 4 containers. Then:
- keep the isolates whose complete genomes the Illumina reads support;
- replace failing isolates from `evidence/ecor_samples.tsv`, or switch truth to the FDA drafts
  plus reads;
- continue with graph construction.

## Data location

Modal Volume `colorframe-bioval`:
- `raw/<dataset>/<sample>/` holds the verified downloads, each with a `.fetch.json`;
- `work/` holds the unpacked genomes and alignments.

Nothing large is in Git. `raw/debourcy2014/reference/CP000948.1.fasta` is a superseded leftover
from the first attempt and is not used.
