# v1.0.1 Remediation Plan

Input: `private/ColorFrame_Independent_Review_2026-11-15.md` (not distributed) and the lead's
v1.0.1 mission. Branch `remediation/v1.0.1`; `main` and `v1.0.0` untouched. Status per item:
`REMEDIATION_STATUS.md`.

| # | Problem (review finding) | Files | Correction | Tests first | Acceptance |
|---|---|---|---|---|---|
| R1 | `search_ms` not phase-equivalent; Rust policy order differs (A) | `python/colorframe.py`, `cpp/src/*`, `rust/src/*`, schema, spec | six phases; sorting moved to `canonicalize`; strict then permissive everywhere | `tests/test_timing_contract.py`; per-language order and emission-order unit tests | all contracts pass; outputs byte-identical to v1.0.0 |
| R2 | Modal peak RSS floor (review §4.5) | `benchmarks/run_benchmarks.py`, `modal_app.py` | `/usr/bin/time` wrapper; record floor and interpreter baselines | `tests/test_rss_measurement.py` (passes on macOS and in the Modal container) | no floor artefact; baselines recorded |
| R3 | RQ1 counts spurious colours as evidence (B) | `benchmarks/generate_workloads.py`, `evaluate_rq1.py` | explicit `p_true_observation` / `p_spurious_colour`; clean and noisy conditions; true-sample metrics; policy ceilings | `tests/test_rq1_model.py` (12 cases) | all pass; perf/stress inputs unchanged |
| R4 | RQ1 single realisation (C) | generator, `analysis/analysis.R` | 10 paired replicates, common random numbers; mean/SD/median/IQR/95% t-interval | determinism and pairing tests | stats table and figure regenerated |
| R5 | Release ZIP contained private material (D) | release process | `git archive` from the release commit plus an archive checker | `tests/check_release_archive.py` | checker passes on the release archive |
| R6 | Prior art incomplete (E) | `LITERATURE_REVIEW.md`, `PRIOR_ART_AND_SCOPE.md`, `references.bib` | ggCaller read in full; verified references | – | every reference verified at a primary source |
| R7 | Token accounting framing (F) | `TOKEN_ACCOUNTING.md`, report | descriptive only | – | no inferential RQ4 claim remains |
| R8 | Attribution inconsistent (G) | `AI_USAGE.md` | substantiated, collaborative where appropriate; the lead's edit preserved | – | pending the lead's confirmation |
| R9 | Docs mismatched with code; scale wording; complexity | spec, architecture, charter, protocol, limitations | correct each | – | documents agree with code |
